import tempfile,zipfile,subprocess,shutil,json
from pathlib import Path
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='bcgi_text_zip_') as folder:
    dest=Path(folder)
    with zipfile.ZipFile(root/'BCGI_LABS_v0.5.3_Build20261014.zip') as z: z.extractall(dest)
    shutil.copy2(root/'test_text_writing.py',dest/'test_text_writing.py')
    result=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','--background','--factory-startup','--python',str(dest/'test_text_writing.py')],capture_output=True,text=True)
    print(result.stdout)
    assert result.returncode==0 and 'TEXT_WRITING_TEST_PASS' in result.stdout,result.stderr
    data=json.loads((dest/'text_writing_verification.json').read_text()); data['isolated_zip_directory']='PASS'
    (root/'text_writing_zip_verification.json').write_text(json.dumps(data,indent=2))
