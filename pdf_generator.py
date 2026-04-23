from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

env = Environment(loader=FileSystemLoader("templates"))


def generate_pdf(data, filename):
    template = env.get_template("character.html")
    html = template.render(**data)

    HTML(string=html).write_pdf(filename)

    return filename