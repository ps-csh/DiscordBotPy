
import logging

import opuslib_next
import numpy
import miniaudio

_logger: logging.Logger = logging.getLogger(__name__)

async def opus_encode_audio(filename, sample_rate, channels, frame_size):
    try:
        # Persistent state for the stream
        encoder = opuslib_next.Encoder(sample_rate, channels, 'audio')
        stream = miniaudio.stream_file(filename, sample_rate=sample_rate, 
                                        nchannels=channels, 
                                        output_format=miniaudio.SampleFormat.SIGNED16)
        
        sequence = 0
        timestamp = 0
        bytes_per_frame = frame_size * channels * 2
        residual = b"" # Buffer for leftover data between chunks

        for pcm_chunk in stream:
            # Combine residual data with the new chunk
            pcm_bytes = residual + pcm_chunk.tobytes()
            
            # Process full frames
            for i in range(0, (len(pcm_bytes) // bytes_per_frame) * bytes_per_frame, bytes_per_frame):
                frame = pcm_bytes[i:i + bytes_per_frame]
                opus_packet = encoder.encode(frame, frame_size)
                yield opus_packet, sequence, timestamp
                
                sequence += 1  # Corrected increment
                timestamp += frame_size

            # Save the remainder for the next loop iteration
            residual = pcm_bytes[(len(pcm_bytes) // bytes_per_frame) * bytes_per_frame:]

        # Optional: Pad and send the final residual if audio ends
        if residual:
            final_frame = residual.ljust(bytes_per_frame, b'\0')
            yield encoder.encode(final_frame, frame_size), sequence, timestamp

    except Exception as e:
        _logger.error(f"Error encoding opus data: {e}")
