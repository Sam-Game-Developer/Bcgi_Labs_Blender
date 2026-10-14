"""Test the shipping ZIP from an isolated directory, as on a new computer."""
import tempfile,zipfile,subprocess,shutil,json
from pathlib import Path
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='bcgi_overlay_zip_') as folder:
    dest=Path(folder)
    with zipfile.ZipFile(root/'BCGI_LABS_v0.5.1_Build20261014.zip') as z: z.extractall(dest)
    shutil.copy2(root/'test_camera_overlay.py',dest/'test_camera_overlay.py')
    result=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','--background','--factory-startup','--python',str(dest/'test_camera_overlay.py')],capture_output=True,text=True)
    print(result.stdout)
    if result.stderr: print(result.stderr)
    assert result.returncode==0 and 'CAMERA_OVERLAY_TEST_PASS' in result.stdout
    data=json.loads((dest/'camera_overlay_verification.json').read_text())
    data['isolated_zip_install_directory']='PASS'
    (root/'camera_overlay_zip_verification.json').write_text(json.dumps(data,indent=2))
