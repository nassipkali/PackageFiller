import os
import sys
import yaml
import hashlib
import requests
from string import Template

print(len(sys.argv))

if len(sys.argv) != 2:
    print("Usage: python main.py <*.yml>")
    sys.exit(1)

class quoted(str):
    pass

def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
yaml.add_representer(quoted, quoted_presenter)

optional_content = """
# Set compiler flags for x86_64 architecture
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=haswell")
endif()

# Set compiler flags for armv7 architecture
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "armv7")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=armv7")
endif()

# Set compiler flags for armv8 architecture
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "armv8")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=armv8-a")
endif()
"""

def calculate_sha256(url):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        sha256_hash = hashlib.sha256()
        for chunk in response.iter_content(4096):
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    else:
        raise Exception(f"Failed to download file from URL: {url}")

#Initialization of required content files
template_path = "./conanfile.template"

with open(template_path, 'r') as file:
    conanfile_template = file.read()

testconanfile_path = "./test_conanfile.py"

with open(testconanfile_path, 'r') as file:
    testconanfile_content = file.read()

testcmakefile_path = "./test_cmakefile.template"

with open(testcmakefile_path, 'r') as file:
    testcmakefile_content = file.read()

with open("test_package.cpp", 'r') as file:
    test_package_cpp = file.read()

root_dir = "recipes"

if not os.path.exists(root_dir):
    os.mkdir(root_dir)
else:
    print(f"The directory '{root_dir}' already exists.")

with open(sys.argv[1], "r") as f:
    config = yaml.safe_load(f)

# Extract values from YAML
package_name = config.get("package_name")
package_altname = config.get("cmake_targetname")
package_version = config.get("package_version")
package_license = config.get("package_license")
package_url = config.get("package_url")
package_simd = config.get("package_simd")

os.chdir("./" + root_dir)

is_simd = False
if package_simd == "yes":
    is_simd = True

package_dependencies = config.get("package_dependencies", [])

package_sha256 = calculate_sha256(package_url)

if "." in package_altname:
    package_classname = "".join(package_altname.split(".")) + "Conan(ConanFile):"
else:
    package_classname = package_altname.capitalize() + "Class"

config_data = {
    'versions': {
        quoted(package_version): {
            'folder': 'all'
        }
    }
}

# Create package dir
if not os.path.exists(package_name):
    os.mkdir(package_name)
else:
    print(f"The directory '{package_name}' already exists.")

os.chdir("./" + package_name)

config_file = 'config.yml'

# Write the data to the config YAML file
with open(config_file, 'w') as file:
    yaml.dump(config_data, file)

content_folder = "all"

# Create package content dir
if not os.path.exists(content_folder):
    os.mkdir(content_folder)
else:
    print(f"The directory '{content_folder}' already exists.")

os.chdir("./" + content_folder)

conan_data = {
    'sources': {
        quoted(package_version): {
            'source': {
                'url': quoted(package_url),
                'sha256': quoted(package_sha256)
            }
        }
    }
}

conandata_file = 'conandata.yml'

# Write the data to the config YAML file
with open(conandata_file, 'w') as file:
    yaml.dump(conan_data, file)

# Handle dependencies
package_dependencies = ['self.requires(\'' + item + '\')' for item in package_dependencies]
indented_strings = [" " * 4 * 2 + s + "\n" for s in package_dependencies]
result = ''.join(indented_strings)

# Using template for fill conanfile.py
template = Template(conanfile_template)

filled_template = template.substitute(
        package_name=package_name,
        package_classname=package_classname,
        package_license=package_license,
        package_altname=package_altname,
        package_dependencies=result
    )

# Specify the file path where you want to save the filled template
output_file_path = "conanfile.py"

# Write the filled template to the file
with open(output_file_path, 'w') as file:
    file.write(filled_template)

print("Filled template has been written to:", output_file_path)

test_folder = "test_package"

# Create package test dir
if not os.path.exists(test_folder):
    os.mkdir(test_folder)
else:
    print(f"The directory '{test_folder}' already exists.")

os.chdir("./" + test_folder)

test_conanfile = "conanfile.py"

with open(test_conanfile, 'w') as file:
    file.write(testconanfile_content)

template2 = Template(testcmakefile_content)
if is_simd:
    filled_template2 = template2.substitute(
            optional_content=optional_content,
            package_altname=package_altname
        )
else:
    filled_template2 = template2.substitute(
            optional_content="",
            package_altname=package_altname
        )

cmakefile = "CMakeLists.txt"

with open(cmakefile, 'w') as file:
    file.write(filled_template2)

with open("test_package.cpp", 'w') as file:
    file.write(test_package_cpp)
