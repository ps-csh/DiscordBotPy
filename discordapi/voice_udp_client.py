import logging
import socket
import asyncio
import struct
import time
import nacl.secret

from discordapi.opus_encoder import opus_encode_audio

_logger: logging.Logger = logging.getLogger(__name__)

async def run_udp_discovery(server_ip, server_port, ssrc):
    loop = asyncio.get_running_loop()
    _logger.debug(f"Running UDP Discovery on {server_ip}:{server_port}, SSRC: {ssrc}")
    # Create an async UDP transport/protocol
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DiscordVoiceDatagramProtocol(ssrc),
        remote_addr=(server_ip, server_port)
    )
    
    try:
        # Wait for the protocol to receive the response
        external_ip, external_port = await protocol.discovery_future
        return external_ip, external_port, protocol
    except BaseException as e:
        _logger.error(f"Failed to get external IP in UDP dicovery: {e}")
    finally:
        #NOTE - we don't want the transport to be closed yet, so we can reuse it for sending data
        #transport.close()
        pass


class DiscordVoiceDatagramProtocol(asyncio.DatagramProtocol):
    _ip_address: str
    _port: int
    _transport = asyncio.DatagramTransport
    discovery_future: any
    _secret: list
    _srrc: int

    def __init__(self, ssrc):
        self._srrc = ssrc
        self._transport = None
        self.discovery_future = asyncio.get_running_loop().create_future()
        self._secret = []
        _logger.debug("Init DiscordVoiceDatagramProtocol")

    def connection_made(self, transport):
        self._transport = transport
        # Build and send the 74-byte packet immediately upon "connection"
        #Format string: > (Big endian), H unsigned short, I unsigned int
        #NOTE - the Discord docs are wrong, and the packet should be 74 bytes, not 70
        packet = struct.pack(">HHI", 0x01, 70, self._srrc) + b"\x00" * 66
        _logger.debug(f"UDP Discovery Packet {packet}")
        _logger.debug(f"UDP Discovery Bytes { int.from_bytes(packet[0:2], byteorder='big')}, {int.from_bytes(packet[2:4], byteorder='big')}, {int.from_bytes(packet[4:8], byteorder='big')}")
        transport.sendto(packet)

    def datagram_received(self, data, addr):
        # 2. Handle the 74-byte discovery response
        _logger.debug(f"Datagram received: {data}, from {addr}")
        if len(data) == 74 and not self.discovery_future.done():
            ip_bytes = data[8:68].split(b'\x00')[0]
            self._ip_address = ip_bytes.decode('ascii')
            #self._ip_address = data[8:data.find(b"\x00", 8)].decode("ascii")
            self._port = struct.unpack("<H", data[-2:])[0]
            self.discovery_future.set_result((self._ip_address, self._port))
            _logger.debug(f"Datagram received: ssrc {struct.unpack(">I", data[4:8])}")
        else:
            _logger.warning(f"Failed to parse datagram from UDP socket: {data}")

    async def send_audio_file(self, filename, sample_rate:int, channels:int, frame_duration:int):
        try:
        # 3. Use the same transport to send your audio frames
            if self._transport:
                _logger.debug(f"Attempting to encode {filename}")
                # Combine RTP Header + Encrypted Audio (AEAD mode)
                frame_size = int(sample_rate * frame_duration / 1000)
                next_time = time.perf_counter()
                async for opus_packet, sequence, timestamp in opus_encode_audio(filename,
                                                                        sample_rate,
                                                                        channels,
                                                                        frame_size):
                    packet = await self.encode_audio_packet(opus_packet, sequence, timestamp)
                    self._transport.sendto(packet)
                    # 3. Precise wait until the next_time is reached
                    # Sleep for most of the duration to save CPU
                    time_to_wait = next_time - time.perf_counter()
                    if time_to_wait > 0.005:
                        time.sleep(time_to_wait - 0.002) # Wake up 2ms early
                        
                    # 4. "Busy-wait" for the final sub-millisecond precision
                    while time.perf_counter() < next_time:
                        pass
        except BaseException as e:
            _logger.error(f"Received error sending audio file: {e}")

    async def encode_audio_packet(self, opus_packet, sequence, timestamp):
        # 1. Prepare the RTP Header (12 bytes)
        # Format: >BBHII (Big-endian: Version/Flags, Payload Type, Seq, Timestamp, SSRC)
        header = bytearray(12)
        header[0] = 0x80  # Version 2
        header[1] = 0x78  # Payload Type (Discord uses 120/0x78)
        struct.pack_into('>H', header, 2, sequence)   # Increments per packet
        struct.pack_into('>I', header, 4, timestamp)  # Increments by FRAME_SIZE (960)
        struct.pack_into('>I', header, 8, self._srrc)       # Provided by Discord

        # 2. Prepare the Nonce (24 bytes for XSalsa20)
        # Discord creates the nonce by taking the 12-byte RTP header and 
        # appending 12 null bytes (0x00).
        nonce = bytes(header + b'\x00' * 12)

        # 3. Encrypt the Opus data
        # 'secret_key' is the 32-byte key from Discord's Opcode 4 (Session Description)
        key_bytes = bytes(self._secret)
        box = nacl.secret.SecretBox(key_bytes)
        encrypted_opus = box.encrypt(opus_packet, nonce).ciphertext

        # 4. Final Packet
        # Send this final byte string over your UDP socket
        return header + encrypted_opus

    def error_received(self, exc):
        print(f"UDP Error encountered: {exc}")
        _logger.error(f"UDP Error encountered: {exc}")

    def close(self):
        self._transport.close()