from vault_utils import list_vault_files
import json

path = r"C:\Users\ale_s\Escritura\ScienceFiction"
tree = list_vault_files(path)
print(json.dumps(tree, indent=2))
