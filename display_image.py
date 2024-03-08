from PIL import Image
import rich.color
import rich.console
import rich.style
import click
from rich.layout import Layout
from rich.panel import Panel
from rich.segment import Segment
from rich.markdown import Markdown
from rich.table import Table
from rich import print, inspect
import shutil
import pokebase as pb



from utils import crop_null_rectangle, add_transparency_border, add_empty_line

DOUBLE_PIXEL = "▀"
DOUBLE_PIXEL_REVERSE = "▄"

BACKGROUND_COLOR = rich.color.Color.from_rgb(0, 0, 0)


class ImageDisplay:
    def __init__(self, img : Image.Image, display_background=True):
        self.console = rich.console.Console()
        img = img.convert("RGBA")
        img = crop_null_rectangle(img)
        img = add_transparency_border(img, 1)
        img = add_empty_line(img)
        self.img = img
        self.display_background = display_background
    
    def __rich_console__(self, console, options):
        for y in range(0, self.img.height, 2):
            for x in range(self.img.width):
                p1 = self.img.getpixel((x, y))
                p2 = self.img.getpixel((x, y + 1))
                top_color = rich.color.Color.from_rgb(*p1[:3])
                bottom_color = rich.color.Color.from_rgb(*p2[:3])

                if self.display_background:
                    yield Segment(DOUBLE_PIXEL, style=rich.style.Style(color=top_color, bgcolor=bottom_color))
                elif not top_color == BACKGROUND_COLOR and not bottom_color == BACKGROUND_COLOR:
                    yield Segment(DOUBLE_PIXEL, style=rich.style.Style(color=top_color, bgcolor=bottom_color))
                elif top_color == BACKGROUND_COLOR and not bottom_color == BACKGROUND_COLOR:
                    yield Segment(DOUBLE_PIXEL_REVERSE, style=rich.style.Style(color=bottom_color))
                elif not top_color == BACKGROUND_COLOR and bottom_color == BACKGROUND_COLOR:
                    yield Segment(DOUBLE_PIXEL, style=rich.style.Style(color=top_color))
                else:
                    yield Segment(" ")
            yield Segment.line()
    


def sort_by_version(x):
    return x.version.url.split("/")[-2]


def get_pokemon_info(pokemon_id, language='en'):
    pokemon_info = pb.pokemon(pokemon_id)
    pokemon_species = pb.pokemon_species(pokemon_id)
    pokemon_sprites = pb.SpriteResource("pokemon", pokemon_id)
    img = Image.open(pokemon_sprites.path)

    names = pokemon_species.names
    descriptions = pokemon_species.flavor_text_entries

    # try to find the name in the requested language
    # fallback to english if not found
    names_lang = [n.name for n in names if n.language.name == language]
    if len(names_lang) == 0:
        names_lang = [n.name for n in names if n.language.name == 'en']
    name = names_lang[0]


    descriptions_lang = [d for d in descriptions if d.language.name == language]
    if len(descriptions_lang) == 0:
        descriptions_lang = [d for d in descriptions if d.language.name == 'en']
    descriptions_lang.sort(key=lambda x: sort_by_version(x))
    description = descriptions_lang[0].flavor_text

    types = pokemon_info.types
    l_types = []
    for t in types:
        type_data = pb.type_(t.type.id_)
        names = type_data.names
        names_lang = [n.name for n in names if n.language.name == language]
        if len(names_lang) == 0:
            names_lang = [n.name for n in names if n.language.name == 'en']
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



def display_pokemon(pokemon_id, language, display_background):
    console = rich.console.Console()

    pokemon_info = get_pokemon_info(pokemon_id, language)

    image_display = ImageDisplay(pokemon_info['img'], display_background)
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


@click.command(name="pokeinfo")
@click.option('--language', '-l', default='en', help='Language to display the pokemon name / description')
@click.option('--pokemon_id', '-p', default=None, multiple=True, type=int, help='Pokemon ids to display, can be multiple.')
@click.option('--display-background', '-d', is_flag=True, help='Display the background of the image as black pixels.')
def main(language, pokemon_id, display_background):
    if pokemon_id:
        for p in pokemon_id:
            display_pokemon(p, language, display_background)
    else:
        print(":cross_mark: [dark_red]No pokemon id provided[/dark_red]")
        # display the help
        print(main.get_help(click.Context(main)))
    
if __name__ == '__main__':
    main()
