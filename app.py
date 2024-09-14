import rasterio
import numpy as np
import os
import glob
from PIL import Image
from pyproj import Transformer

# Caminho para a imagem .tiff grande e pastas de saída
tiff_path = glob.glob("img/tiff/*.tif")
image_output_dir = "img/tiff_imagem"

tile_size = 1012  # Ajuste o tamanho dos blocos

# Função para obter latitude e longitude de um tile
def extract_tile_coordinates(src, window):
    # Obtenha a transformação da imagem
    transform = src.transform
    # Obtenha as coordenadas dos cantos da janela
    row_start, col_start = window.row_off, window.col_off
    row_end, col_end = row_start + window.height, col_start + window.width

    # Coordenadas dos cantos da janela (pixel-to-world)
    lon_min, lat_max = transform * (col_start, row_start)  # Canto superior esquerdo
    lon_max, lat_min = transform * (col_end, row_end)  # Canto inferior direito
    
    # Transforme as coordenadas para sistema geográfico
    transformer = Transformer.from_crs(src.crs, 'EPSG:4326', always_xy=True)
    west, south = transformer.transform(lon_min, lat_min)
    east, north = transformer.transform(lon_max, lat_max)
    
    return west, south, east, north

# Criar diretório de saída se não existir
os.makedirs(image_output_dir, exist_ok=True)

# Função para converter o tile TIFF em imagem
def convert_tiff_tile_to_image(tile, image_path):
    if tile.shape[0] >= 3:
        # Pegue as 3 primeiras bandas (geralmente correspondem a R, G, B)
        r = tile[0]  # Banda 1 (R)
        g = tile[1]  # Banda 2 (G)
        b = tile[2]  # Banda 3 (B)

        # Verifique se as bandas são válidas
        if r.max() == 0 and g.max() == 0 and b.max() == 0:
            # print(f"Tile contém apenas zeros. Ignorando.")
            return

        # Normalizar valores para faixa de 0-255 se necessário
        if r.max() > 0:
            r = (r / r.max()) * 255
        if g.max() > 0:
            g = (g / g.max()) * 255
        if b.max() > 0:
            b = (b / b.max()) * 255
        
        # Combine as bandas em uma imagem RGB
        rgb_image = np.stack((r, g, b), axis=-1).astype(np.uint8)
        
        # Crie a imagem PIL a partir da matriz numpy
        img = Image.fromarray(rgb_image)
        img.save(image_path)

# Abrir o arquivo TIFF original
with rasterio.open(tiff_path[0]) as src:
    width, height = src.width, src.height

    # Quebrar em tiles
    for i in range(0, width, tile_size):
        for j in range(0, height, tile_size):
            window = rasterio.windows.Window(i, j, tile_size, tile_size)
            tile = src.read(window=window)

            # Obter coordenadas geográficas do tile atual
            west, south, east, north = extract_tile_coordinates(src, window)
            
            # Gerar nome do arquivo com latitude e longitude dos cantos do tile
            image_filename = f"{west:.6f}_{south:.6f}_{east:.6f}_{north:.6f}.png"
            image_path = os.path.join(image_output_dir, image_filename)

            # Converter o tile TIFF em imagem (PNG/JPG)
            convert_tiff_tile_to_image(tile, image_path)

            # Apagar o tile TIFF após a conversão para imagem
            print(f"Imagem {image_filename} salva.")
            
print("Processo concluído!")
