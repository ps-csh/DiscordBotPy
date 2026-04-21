
import opuslib_next
import numpy
import miniaudio


async def opus_encode_audio(filename, sample_rate, channels, frame_size):
    # application types include 'voip', 'audio' and 'restricted_lowdelay'
    async with opuslib_next.Encoder(sample_rate, channels, 'audio') as encoder:

        stream = miniaudio.stream_file(filename,
                                        sample_rate=sample_rate,
                                        nchannels=channels,
                                        output_format=miniaudio.SampleFormat.SIGNED16)
        sequence, timestamp = 0
        
        # Miniaudio yields 'array.array' objects of PCM data
        for pcm_chunk in stream:
            # pcm_chunk might contain multiple frames. We need to slice it 
            # into exactly FRAME_SIZE (960) chunks for the encoder.
            pcm_bytes = pcm_chunk.tobytes()
            
            # 960 samples * 2 channels * 2 bytes per sample = 3840 bytes per 20ms
            bytes_per_frame = frame_size * channels * 2
            
            for i in range(0, len(pcm_bytes), bytes_per_frame):
                frame = pcm_bytes[i:i + bytes_per_frame]
                
                # Pad the final frame with silence if it's too short
                if len(frame) < bytes_per_frame:
                    frame = frame.ljust(bytes_per_frame, b'\0')
                
                # Encode to Opus
                opus_packet = encoder.encode(frame, frame_size)
                yield opus_packet, sequence, timestamp
                sequence += sequence
                timestamp += frame_size
    pass