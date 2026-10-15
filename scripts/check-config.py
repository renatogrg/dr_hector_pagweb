"""Exercise integrations with isolated test data, never production artifacts."""
import json, os, subprocess, tempfile
from pathlib import Path
project=Path(__file__).resolve().parent.parent
original=json.loads((project/'medical.config.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='medical-site-check-') as temporary:
    folder=Path(temporary)
    config=json.loads(json.dumps(original))
    config['clinic'].update(name='CONSULTORIO DE PRUEBA',streetAddress='DIRECCIÓN DE PRUEBA',city='CIUDAD DE PRUEBA',country='PE',phone='+51999999999',whatsapp='+51999999999',mapsUrl='https://www.google.com/maps?q=prueba',hours=[{'days':['Monday'],'opens':'09:00','closes':'17:00'}])
    config['editorial'].update(reviewer='REVISOR DE PRUEBA',reviewed='2026-10-08')
    config.update(analyticsId='G-TEST123',searchConsoleVerification='TOKEN-DE-PRUEBA',allowAITraining=False)
    config_path=folder/'fixture.json'
    config_path.write_text(json.dumps(config),encoding='utf-8')
    for base in ('https://example.org/','https://example.org/proyecto/'):
        output=folder/'output'
        environment={**os.environ,'MEDICAL_CONFIG':str(config_path),'DIST_DIR':str(output),'SITE_URL':base}
        subprocess.run(['python',str(project/'generate.py')],env=environment,check=True)
        subprocess.run(['python',str(project/'scripts/check-seo.py')],env=environment,check=True)
        contact=(output/'contacto/index.html').read_text(encoding='utf-8')
        for required in ('tel:+51999999999','https://wa.me/51999999999','google-site-verification','TOKEN-DE-PRUEBA','analytics-accept','data-whatsapp','MedicalClinic','practicesAt'):
            assert required in contact, required
        assert 'User-agent: GPTBot\nDisallow: /' in (output/'robots.txt').read_text()
    print('Configuración: dominio/subdirectorio, NAP, consultorio, revisor, Search Console, canales y entrenamiento probados en archivos temporales.')
