from setuptools import setup, find_packages
setup(
    name="railway",
    version="0.3.0",
    packages=find_packages(),
    entry_points={
    	"console_scripts":[
    		"railway = lib:run"
    	]
    }
)