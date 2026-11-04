import ctypes, numpy as np, wave, sys, espeakng_loader as E
lib = ctypes.CDLL(E.get_library_path())
CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
buf = []
def _cb(wav, n, ev):
    if n > 0: buf.append(np.ctypeslib.as_array(wav, (n,)).copy())
    return 0
cb = CB(_cb)
sr = lib.espeak_Initialize(1, 500, E.get_data_path().encode(), 0)
lib.espeak_SetSynthCallback(cb)
def say(text, out, voice='ru', rate=150, pitch=35, rng=40):
    buf.clear()
    lib.espeak_SetVoiceByName(voice.encode())
    lib.espeak_SetParameter(1, rate, 0); lib.espeak_SetParameter(3, pitch, 0); lib.espeak_SetParameter(4, rng, 0)
    b = text.encode('utf-8')
    lib.espeak_Synth(b, len(b) + 1, 0, 1, 0, 1, None, None)
    lib.espeak_Synchronize()
    a = np.concatenate(buf) if buf else np.zeros(1, np.int16)
    w = wave.open(out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.astype(np.int16).tobytes()); w.close()
    return len(a) / sr
if __name__ == '__main__':
    print(sr, say(sys.argv[1], sys.argv[2]))
