import re
import json

def update_file(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update the select options
    new_select_options = """<select id="region" name="region" required class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-colors appearance-none cursor-pointer">
                    <option value="">Selecciona</option>
                    <option value="arica">Región de Arica y Parinacota</option>
                    <option value="tarapaca">Región de Tarapacá</option>
                    <option value="antofagasta">Región de Antofagasta</option>
                    <option value="coquimbo">Región de Coquimbo</option>
                    <option value="valparaiso">Región de Valparaíso</option>
                    <option value="metropolitana">Región Metropolitana</option>
                    <option value="ohiggins">Región de O'Higgins</option>
                    <option value="maule">Región del Maule</option>
                    <option value="nuble">Región de Ñuble</option>
                    <option value="biobio">Región del Bío-Bío</option>
                    <option value="araucania">Región de La Araucanía</option>
                    <option value="losrios">Región de Los Ríos</option>
                    <option value="loslagos">Región de Los Lagos</option>
                </select>"""

    pattern_select = r'<select id="region" name="region" required class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-colors appearance-none cursor-pointer">.*?</select>'
    
    html, count_select = re.subn(pattern_select, new_select_options, html, flags=re.DOTALL)
    print(f"  Replaced select options: {count_select} occurrence(s)")

    # 2. Update the JS object with all regions
    new_js_object = """const comunasPorRegion = {
    "arica": ["Arica", "Camarones", "Putre", "General Lagos"],
    "tarapaca": ["Iquique", "Alto Hospicio", "Pozo Almonte", "Camiña", "Colchane", "Huara", "Pica"],
    "antofagasta": ["Antofagasta", "Mejillones", "Sierra Gorda", "Taltal", "Calama", "Ollagüe", "San Pedro de Atacama", "Tocopilla", "María Elena"],
    "coquimbo": ["La Serena", "Coquimbo", "Andacollo", "La Higuera", "Paiguano", "Vicuña", "Illapel", "Canela", "Los Vilos", "Salamanca", "Ovalle", "Combarbalá", "Monte Patria", "Punitaqui", "Río Hurtado"],
    "valparaiso": ["Valparaíso", "Casablanca", "Concón", "Juan Fernández", "Puchuncaví", "Quintero", "Viña del Mar", "Isla de Pascua", "Los Andes", "Calle Larga", "Rinconada", "San Esteban", "La Ligua", "Cabildo", "Papudo", "Petorca", "Zapallar", "Quillota", "Calera", "Hijuelas", "La Cruz", "Nogales", "San Antonio", "Algarrobo", "Cartagena", "El Quisco", "El Tabo", "Santo Domingo", "San Felipe", "Catemu", "Llaillay", "Panquehue", "Putaendo", "Santa María", "Quilpué", "Limache", "Olmué", "Villa Alemana"],
    "metropolitana": ["Santiago", "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", "Estación Central", "Huechuraba", "Independencia", "La Cisterna", "La Florida", "La Granja", "La Pintana", "La Reina", "Las Condes", "Lo Barnechea", "Lo Espejo", "Lo Prado", "Macul", "Maipú", "Ñuñoa", "Pedro Aguirre Cerda", "Peñalolén", "Providencia", "Pudahuel", "Quilicura", "Quinta Normal", "Recoleta", "Renca", "San Joaquín", "San Miguel", "San Ramón", "Vitacura", "Puente Alto", "Pirque", "San José de Maipo", "Colina", "Lampa", "Tiltil", "San Bernardo", "Buin", "Calera de Tango", "Paine", "Melipilla", "Alhué", "Curacaví", "María Pinto", "San Pedro", "Talagante", "El Monte", "Isla de Maipo", "Padre Hurtado", "Peñaflor"],
    "ohiggins": ["Rancagua", "Codegua", "Coinco", "Coltauco", "Doñihue", "Graneros", "Las Cabras", "Machalí", "Malloa", "Mostazal", "Olivar", "Peumo", "Pichidegua", "Quinta de Tilcoco", "Rengo", "Requínoa", "San Vicente", "Pichilemu", "La Estrella", "Litueche", "Marchigüe", "Navidad", "Paredones", "San Fernando", "Chépica", "Chimbarongo", "Lolol", "Nancagua", "Palmilla", "Peralillo", "Placilla", "Pumanque", "Santa Cruz"],
    "maule": ["Talca", "Constitución", "Curepto", "Empedrado", "Maule", "Pelarco", "Pencahue", "Río Claro", "San Clemente", "San Rafael", "Cauquenes", "Chanco", "Pelluhue", "Curicó", "Hualañé", "Licantén", "Molina", "Rauco", "Romeral", "Sagrada Familia", "Teno", "Vichuquén", "Linares", "Colbún", "Longaví", "Parral", "Retiro", "San Javier", "Villa Alegre", "Yerbas Buenas"],
    "nuble": ["Chillán", "Bulnes", "Cobquecura", "Coelemu", "Coihueco", "Chillán Viejo", "El Carmen", "Ninhue", "Ñiquén", "Pemuco", "Pinto", "Portezuelo", "Quillón", "Quirihue", "Ránquil", "San Carlos", "San Ignacio", "San Nicolás", "Treguaco", "Yungay"],
    "biobio": ["Concepción", "Coronel", "Chiguayante", "Florida", "Hualqui", "Lota", "Penco", "San Pedro de la Paz", "Santa Juana", "Talcahuano", "Tomé", "Hualpén", "Lebu", "Arauco", "Cañete", "Contulmo", "Curanilahue", "Los Álamos", "Tirúa", "Los Ángeles", "Antuco", "Cabrero", "Laja", "Mulchén", "Nacimiento", "Negrete", "Quilaco", "Quilleco", "San Rosendo", "Santa Bárbara", "Tucapel", "Yumbel", "Alto Biobío"],
    "araucania": ["Temuco", "Carahue", "Cunco", "Curarrehue", "Freire", "Galvarino", "Gorbea", "Lautaro", "Loncoche", "Melipeuco", "Nueva Imperial", "Padre las Casas", "Perquenco", "Pitrufquén", "Pucón", "Saavedra", "Teodoro Schmidt", "Toltén", "Vilcún", "Villarrica", "Cholchol", "Angol", "Collipulli", "Curacautín", "Ercilla", "Lonquimay", "Los Sauces", "Lumaco", "Purén", "Renaico", "Traiguén", "Victoria"],
    "losrios": ["Valdivia", "Corral", "Lanco", "Los Lagos", "Máfil", "Mariquina", "Paillaco", "Panguipulli", "La Unión", "Futrono", "Lago Ranco", "Río Bueno"],
    "loslagos": ["Puerto Montt", "Calbuco", "Cochamó", "Fresia", "Frutillar", "Los Muermos", "Llanquihue", "Maullín", "Puerto Varas", "Castro", "Ancud", "Chonchi", "Curaco de Vélez", "Dalcahue", "Puqueldón", "Queilén", "Quellón", "Quemchi", "Quinchao", "Osorno", "Puerto Octay", "Purranque", "Puyehue", "Río Negro", "San Juan de la Costa", "San Pablo", "Chaitén", "Futaleufú", "Hualaihué", "Palena"]
};"""

    pattern_js = r'const comunasPorRegion\s*=\s*\{.*?\};'
    html, count_js = re.subn(pattern_js, new_js_object, html, flags=re.DOTALL)
    print(f"  Replaced JS object: {count_js} occurrence(s)")

    if count_select > 0 and count_js > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Successfully updated {filepath}")
    else:
        print(f"  ERROR: Could not update {filepath} (select: {count_select}, JS: {count_js})")

update_file("index.html")
update_file("index_collagen.html")
