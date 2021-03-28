import requests
from PIL import Image


if __name__ == '__main__':
    url = 'https://www.matchendirect.fr/image/logo/club/128/metz-logo896.png'
    logo = Image.open(requests.get(url, stream=True).raw)
    logo.resize((80, 80))
    background = Image.open("./ressources/images/fond_thumbnail.jpg")
    image = Image.new(mode='RGBA', size=(626, 347), color=(0, 0, 0, 0))
    image.paste(background, (0, 0))
    image.paste(logo, (103, 120), logo)
    image.paste(logo, (393, 120), logo)
    image.save("MonImage.png", "PNG")