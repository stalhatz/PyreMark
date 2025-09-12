from os import path
from flask import Flask, render_template,request, jsonify,send_from_directory

from build import readYamlData

app = Flask(__name__,template_folder="..",static_folder="../js/")


@app.route('/css/<path:filename>')
def css_static(filename):
    path = app.root_path + '/../css/'
    return send_from_directory(path , filename)

@app.route('/img/<path:filename>')
def img_static(filename):
    path = app.root_path + '/../img/'
    return send_from_directory(path , filename)

@app.route('/')
def index():
    return render_template('./j2/index.html.j2')

htmlTemplatesDict = {
    "pre":"./j2/preambule.html.j2",
    "exp":"./j2/experience.html.j2",
    "pub":"./j2/publications.html.j2",
    "pat":"./j2/patents.html.j2",
    "edu":"./j2/education.html.j2",
    "mcr":"./j2/microcredits_list.html.j2",
    "skl": "./j2/competences.html.j2", 
    "lng":"./j2/languages.html.j2"
    }

@app.route('/component')
def component():
    

    sections = request.args.getlist("sections")

    htmlTemplates = []
    htmlTemplates.append(htmlTemplatesDict["pre"])
    for section in sections:
        htmlTemplates.append(htmlTemplatesDict[section])
 


    yamlFileList = [
    "./yaml/resume_partial.yaml",
    "./yaml/agile_course.yaml",
    "./yaml/atelier_cnil.yaml",
    "./yaml/deep_learning.yaml",
    "./yaml/ITIL.yaml",
    "./yaml/Prince2_Foundation.yaml",
    "./yaml/competences.yaml", 
    "./yaml/tableau.yaml",
    "./yaml/exp_sorbonne.yaml",
    "./yaml/exp_inria.yaml",
    "./yaml/exp_toshiba.yaml",
    "./yaml/languages.yaml"
    ]
   
    context = readYamlData(yamlFileList)
    lang = request.args.get('lang', 'en')
    
    context["htmlTemplates"] = htmlTemplates
    print("HtmlTemplates :: " + str(htmlTemplates))
    context["lang"] = lang
    component_html = render_template('./j2/resume_canvas.html.j2',**context)
    component_css = render_template('./j2/resume.css.j2',**context)
    component_js  = render_template('./js/multipage.js')

    return jsonify({
      'html': component_html,
      'css': component_css,
      'js': component_js
    })

if __name__ == '__main__':
    app.run(debug=True)