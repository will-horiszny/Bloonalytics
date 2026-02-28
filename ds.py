import subprocess

# We move most logic into the YAML and keep the command clean
command = [
    "datasette", "serve",
    # "-h", "0.0.0.0",
    "-c", "datasette.yaml",
    "./"
]

subprocess.run(command)