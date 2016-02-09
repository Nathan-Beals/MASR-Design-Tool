from setuptools import setup, find_packages

setup(name='MASR_Design_Tool',
      version='1.0.0',
      #install_requires=['matplotlib'],
      packages=find_packages(),
      package_data={'': ['*.pdf'], 'masr_design_tool': ['databases/*.bak', 'databases/*.dat', 'databases/*.dir']},
      scripts=['runner.py'],
      entry_points={'gui_scripts': ['masr_design_tool = masr_design_tool.main_GUI:main']},
      )