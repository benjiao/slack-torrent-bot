import os
import codecs
import pystache


class ResponseGenerator:
    def __init__(self, template_dir='./templates'):
        self.template_dir = os.path.expanduser(template_dir)
        self.templates = {}
        self.renderer = pystache.Renderer()

        templates = [t for t in os.listdir(template_dir) if t.endswith('.mustache')]
        self.parse_templates(templates)

    def parse_templates(self, templates):
        for template in templates:
            print "Parse template: %s" % os.path.join(self.template_dir, template)

            with codecs.open(os.path.join(self.template_dir, template), 'r', 'utf-8') as content_file:
                content = content_file.read()
                self.templates[template.strip('.mustache')] = pystache.parse(content)

    def response(self, template_name, params):
        parsed_template = self.templates.get(template_name, None)
        if parsed_template is None:
            return ""

        return self.renderer.render(parsed_template, params)
