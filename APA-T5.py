


# Autor: Álvaro Marcos Rodríguez


import struct




def _leer_cabecera(f):
    riff_header = f.read(12)
    if len(riff_header) < 12:
        raise ValueError("Fichero demasiado corto para ser un WAVE válido.")

    riff_id, riff_size, wave_id = struct.unpack('<4sI4s', riff_header)

    if riff_id != b'RIFF':
        raise ValueError(f"No es un fichero RIFF (cabecera: {riff_id}).")
    if wave_id != b'WAVE':
        raise ValueError(f"No es un fichero WAVE (tipo: {wave_id}).")

    fmt_header = f.read(8)
    if len(fmt_header) < 8:
        raise ValueError("Cabecera fmt incompleta.")

    fmt_id, fmt_size = struct.unpack('<4sI', fmt_header)

    if fmt_id != b'fmt ':
        raise ValueError(f"Se esperaba el cacho 'fmt ', encontrado: {fmt_id}.")

    fmt_data = f.read(fmt_size)
    if len(fmt_data) < 16:
        raise ValueError("Datos del cacho fmt insuficientes.")

    (audio_format, num_channels, sample_rate,
     byte_rate, block_align, bits_per_sample) = struct.unpack('<HHIIHH', fmt_data[:16])

    if audio_format != 1:
        raise ValueError(
            f"Solo se admite PCM lineal (formato 1). Formato encontrado: {audio_format}."
        )

    data_header = f.read(8)
    if len(data_header) < 8:
        raise ValueError("Cabecera data incompleta.")

    data_id, data_size = struct.unpack('<4sI', data_header)

    if data_id != b'data':
        raise ValueError(f"Se esperaba el cacho 'data', encontrado: {data_id}.")

    return {
        'riff_id': riff_id,
        'riff_size': riff_size,
        'wave_id': wave_id,
        'fmt_id': fmt_id,
        'fmt_size': fmt_size,
        'audio_format': audio_format,
        'num_channels': num_channels,
        'sample_rate': sample_rate,
        'byte_rate': byte_rate,
        'block_align': block_align,
        'bits_per_sample': bits_per_sample,
        'data_id': data_id,
        'data_size': data_size,
    }


def _escribir_cabecera(f, num_channels, sample_rate, bits_per_sample, data_size):
    block_align = num_channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    fmt_size = 16
    riff_size = 4 + 8 + fmt_size + 8 + data_size

    f.write(struct.pack('<4sI4s', b'RIFF', riff_size, b'WAVE'))
    f.write(struct.pack('<4sI', b'fmt ', fmt_size))
    f.write(struct.pack('<HHIIHH',
                        1,
                        num_channels,
                        sample_rate,
                        byte_rate,
                        block_align,
                        bits_per_sample))
    f.write(struct.pack('<4sI', b'data', data_size))



def estereo2mono(ficEste, ficMono, canal=2):
    
    # Lee un fichero de audio estéreo (16 bits) y genera un fichero monofónico.

    if canal not in (0, 1, 2, 3):
        raise ValueError("El parámetro 'canal' debe ser un entero entre 0 y 3.")
        
    with open(ficEste, 'rb') as f_entrada:
        meta = leer_cabecera_wave(f_entrada)
        
        if meta['canales'] != 2:
            raise ValueError("El fichero de origen debe ser estéreo (2 canales).")
        if meta['bits_muestra'] != 16:
            raise ValueError("Solo se admiten ficheros estéreo con resolución de 16 bits.")
        if meta['formato'] != 1:
            raise ValueError("El formato de codificación debe ser PCM lineal.")
            
        datos_crudos = f_entrada.read(meta['tamano_datos'])
        
    total_muestras_estereo = len(datos_crudos) // 2
    muestras = struct.unpack(f'<{total_muestras_estereo}h', datos_crudos)
    
    izq = muestras[0::2]
    der = muestras[1::2]
    
    if canal == 0:
        muestras_mono = izq
    elif canal == 1:
        muestras_mono = der
    elif canal == 2:
        muestras_mono = [(l + r) // 2 for l, r in zip(izq, der)]
    else:  # canal == 3
        muestras_mono = [(l - r) // 2 for l, r in zip(izq, der)]
        
    num_muestras_final = len(muestras_mono)
    datos_salida = struct.pack(f'<{num_muestras_final}h', *muestras_mono)
    
    with open(ficMono, 'wb') as f_salida:
        escribir_cabecera_wave(f_salida, 1, meta['frecuencia'], 16, len(datos_salida))
        f_salida.write(datos_salida)

        def mono2estereo(ficIzq, ficDer, ficEste):
    
   # Fusiona dos ficheros monofónicos de 16 bits en un único fichero estéreo de 16 bits.
   
    with open(ficIzq, 'rb') as f_izq:
        meta_i = leer_cabecera_wave(f_izq)
        if meta_i['canales'] != 1 or meta_i['bits_muestra'] != 16 or meta_i['formato'] != 1:
            raise ValueError("El archivo izquierdo debe ser mono, PCM, de 16 bits.")
        datos_izq = f_izq.read(meta_i['tamano_datos'])
        
    with open(ficDer, 'rb') as f_der:
        meta_d = leer_cabecera_wave(f_der)
        if meta_d['canales'] != 1 or meta_d['bits_muestra'] != 16 or meta_d['formato'] != 1:
            raise ValueError("El archivo derecho debe ser mono, PCM, de 16 bits.")
        datos_der = f_der.read(meta_d['tamano_datos'])
        
    if meta_i['frecuencia'] != meta_d['frecuencia']:
        raise ValueError("Las frecuencias de muestreo de ambos archivos no coinciden.")
        
    muestras_izq = struct.unpack(f'<{len(datos_izq) // 2}h', datos_izq)
    muestras_der = struct.unpack(f'<{len(datos_der) // 2}h', datos_der)
    
    min_muestras = min(len(muestras_izq), len(muestras_der))
    
    # Intercalación mediante comprensión plana unidimensional
    intercaladas = [
        muestra
        for i in range(min_muestras)
        for muestra in (muestras_izq[i], muestras_der[i])
    ]
    
    datos_salida = struct.pack(f'<{min_muestras * 2}h', *intercaladas)
    
    with open(ficEste, 'wb') as f_salida:
        escribir_cabecera_wave(f_salida, 2, meta_i['frecuencia'], 16, len(datos_salida))
        f_salida.write(datos_salida)
        def codEstereo(ficEste, ficCod):
    """
    Codifica un fichero estéreo de 16 bits en un fichero de 32 bits (monofónico).
    Almacena la semisuma en la parte alta (MSB) y la semidiferencia en la baja (LSB).
    """
    with open(ficEste, 'rb') as f_entrada:
        meta = leer_cabecera_wave(f_entrada)
        if meta['canales'] != 2 or meta['bits_muestra'] != 16 or meta['formato'] != 1:
            raise ValueError("El archivo de entrada debe ser estéreo PCM de 16 bits.")
        datos_crudos = f_entrada.read(meta['tamano_datos'])
        
    muestras = struct.unpack(f'<{len(datos_crudos) // 2}h', datos_crudos)
    izq = muestras[0::2]
    der = muestras[1::2]
    
    datos_32 = [
        (((l + r) // 2) << 16) | (((l - r) // 2) & 0xFFFF)
        for l, r in zip(izq, der)
    ]
    
    datos_salida = struct.pack(f'<{len(datos_32)}i', *datos_32)
    
    with open(ficCod, 'wb') as f_salida:
        escribir_cabecera_wave(f_salida, 1, meta['frecuencia'], 32, len(datos_salida))
        f_salida.write(datos_salida)
        def decEstereo(ficCod, ficEste):
    
    # Decodifica una señal de 32 bits para extraer y restaurar los dos canales de 16 bits.
    
    with open(ficCod, 'rb') as f_entrada:
        meta = leer_cabecera_wave(f_entrada)
        if meta['canales'] != 1 or meta['bits_muestra'] != 32:
            raise ValueError("El archivo codificado debe ser monofónico de 32 bits.")
        datos_crudos = f_entrada.read(meta['tamano_datos'])
        
    num_muestras = len(datos_crudos) // 4
    muestras_32 = struct.unpack(f'<{num_muestras}i', datos_crudos)
    
    semisuma = [v >> 16 for v in muestras_32]
    semidif = [((v & 0xFFFF) ^ 0x8000) - 0x8000 for v in muestras_32]
    
    limitar = lambda x: max(-32768, min(32767, x))
    
    # Comprensión  para reconstruir, limitar e intercalar 
    intercalado = [
        limitar(val)
        for s, d in zip(semisuma, semidif)
        for val in (s + d, s - d)
    ]
    
    datos_salida = struct.pack(f'<{num_muestras * 2}h', *intercalado)
    
    with open(ficEste, 'wb') as f_salida:
        escribir_cabecera_wave(f_salida, 2, meta['frecuencia'], 16, len(datos_salida))
        f_salida.write(datos_salida)