import rasterio
import numpy as np
import os
from PIL import Image

# Caminho para a imagem .tiff grande e pastas de saída
tiff_path = "img/tiff/a.tif"
tiff_output_dir = "img/tiff_quebrado"
image_output_dir = "img/tiff_imagem"

tile_size = 512  # Ajuste o tamanho dos blocos

# Função para obter latitude e longitude de um tile
def get_lat_lon(transform, x, y):
    lon, lat = transform * (x + 0.5, y + 0.5)  # Ponto central do tile
    return lat, lon


# Criar diretório de saída se não existir
os.makedirs(image_output_dir, exist_ok=True)

# Abrir o arquivo TIFF original
with rasterio.open(tiff_path) as src:
    width, height = src.width, src.height
    transform = src.transform

    # Verifique quantas bandas a imagem possui
    print(f"Número de bandas: {src.count}")

    # Quebrar em tiles
    for i in range(0, width, tile_size):
        for j in range(0, height, tile_size):
            window = rasterio.windows.Window(i, j, tile_size, tile_size)
            tile_transform = src.window_transform(window)
            tile = src.read(window=window)
            
            # Obter a latitude e longitude para os cantos Norte, Sul, Leste e Oeste
            lat, lon = get_lat_lon(transform, i, j)
            
            # Gerar nome do arquivo com latitude, longitude e direções
            image_filename = f"{lat:.6f}_{lon:.6f}.png"
            image_path = os.path.join(image_output_dir, image_filename)

            # Converter o tile TIFF em imagem (PNG/JPG)
            if src.count >= 3:
                # Pegue as 3 primeiras bandas (geralmente correspondem a R, G, B)
                r = tile[0]  # Banda 1 (R)
                g = tile[1]  # Banda 2 (G)
                b = tile[2]  # Banda 3 (B)

                # Verifique se as bandas são válidas
                if r.max() == 0 and g.max() == 0 and b.max() == 0:
                    print(f"Tile em {i}, {j} contém apenas zeros. Ignorando.")
                    continue

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

            # Apagar o tile TIFF após a conversão para imagem
            print(f"Imagem {image_filename} salva e arquivo TIFF correspondente apagado.")
            
print("Processo concluído!")
