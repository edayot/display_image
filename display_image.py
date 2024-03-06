from PIL import Image
import rich.color
import rich.console
import rich.style
import click
from rich.layout import Layout
from rich.panel import Panel
from rich import print as rprint
from rich.segment import Segment
from rich.markdown import Markdown
from rich.table import Table
from rich.columns import Columns
import shutil
import requests
import rich.__main__


from utils import crop_null_rectangle, add_transparency_border, add_empty_line

DOUBLE_PIXEL = "▀"


class ImageDisplay:
    def __init__(self, img : Image.Image):
        self.console = rich.console.Console()
        img = img.convert("RGBA")
        img = crop_null_rectangle(img)
        img = add_transparency_border(img, 1)
        img = add_empty_line(img)
        self.img = img
    
    def __rich_console__(self, console, options):
        for y in range(0, self.img.height, 2):
            for x in range(self.img.width):
                p1 = self.img.getpixel((x, y))
                p2 = self.img.getpixel((x, y + 1))
                foreground = rich.color.Color.from_rgb(*p1[:3])
                background = rich.color.Color.from_rgb(*p2[:3])
                yield Segment(DOUBLE_PIXEL, style=rich.style.Style(color=foreground, bgcolor=background))
            yield Segment.line()
    


def sort_by_version(x):
    return x["version"]["url"].split("/")[-2]


def get_pokemon_info(pokemon_id, language='en'):
    r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    r.raise_for_status()

    data = r.json()
    img = Image.open(requests.get(data['sprites']['front_default'], stream=True).raw)

    species = requests.get(data['species']['url']).json()
    names = species['names']
    descriptions = species['flavor_text_entries']

    # try to find the name in the requested language
    # fallback to english if not found
    names_lang = [n['name'] for n in names if n['language']['name'] == language]
    if len(names_lang) == 0:
        names_lang = [n['name'] for n in names if n['language']['name'] == 'en']
    name = names_lang[0]

    descriptions_lang = [d for d in descriptions if d['language']['name'] == language]
    if len(descriptions_lang) == 0:
        descriptions_lang = [d for d in descriptions if d['language']['name'] == 'en']
    descriptions_lang.sort(key=lambda x: sort_by_version(x))
    description = descriptions_lang[0]["flavor_text"]

    types = data['types']
    l_types = []
    for t in types:
        r = requests.get(t['type']['url'])
        r.raise_for_status()
        type_data = r.json()
        names = type_data['names']
        names_lang = [n['name'] for n in names if n['language']['name'] == language]
        if len(names_lang) == 0:
            names_lang = [n['name'] for n in names if n['language']['name'] == 'en']
        type_name = names_lang[0]
        l_types.append(type_name)
        


    return {
        'name': name,
        'description': description,
        'img': img,
        "types": l_types,
    }


def generate_types_panel(types: list[str]):
    table = Table.grid(padding=1, expand=True)
    table.add_column(justify="center",vertical="middle")
    table.add_row("")
    for t in types:
        table.add_row(f"[{t}]")
    return Panel(table, border_style="blue")



def display_pokemon(pokemon_id, language):
    console = rich.console.Console()

    pokemon_info = get_pokemon_info(pokemon_id, language)

    image_display = ImageDisplay(pokemon_info['img'])
    description = Markdown(
f"""# {pokemon_info['name']} (#{pokemon_id})

{pokemon_info['description']}


""".strip("\n").strip()
    )

    layout = Layout(name="root")
    layout.split_row(
        Layout(Panel(image_display), name="image", size=image_display.img.width + 4),
        Layout(name="desc", size=(35))
    )
    layout["desc"].split_column(
        Layout(Panel(description, border_style="green"), name="description"),
        generate_types_panel(pokemon_info["types"])
    )

    _width, _height = shutil.get_terminal_size()

    _height = image_display.img.height//2 + 2
    console.size = (_width, _height)
    console.print(layout)


@click.command()
@click.option('--language', '-l', default='en', help='Language to display the pokemon name / description')
@click.option('--pokemon_id', '-p', default=None, multiple=True, help='Pokemon ids to display')
def main(language, pokemon_id):
    if pokemon_id:
        for p in pokemon_id:
            display_pokemon(p, language)
    else:
        rprint("No pokemon id provided")
    
if __name__ == '__main__':
    main()
