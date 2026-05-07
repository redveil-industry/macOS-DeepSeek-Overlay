try:
    from setuptools import setup
except:
    class DependencyError(Exception): pass
    raise(DependencyError("Missing python package 'setuptools'.\n  pip install --user setuptools"))

import os
import sys

def read(f_name, empty_lines=False):
    text = []
    with open(os.path.join(package_about, f_name)) as f:
        for line in f:
            line = line.strip("\n")
            if (not empty_lines) and (len(line.strip()) == 0): continue
            if (len(line) > 0) and (line[0] == "%"): continue
            text.append(line)
    return text

source_page = "deepseek"
package_name = f"macos-{source_page}-overlay"
package_about = os.path.join(os.path.dirname(os.path.abspath(__file__)), package_name.replace("-","_"), "about")


if __name__ == "__main__":
    package = package_name.replace("-", "_")
    version = read("version.txt")[0]
    description = read("description.txt")[0]
    keywords = read("keywords.txt")
    classifiers = read("classifiers.txt")
    name, email, git_username = read("author.txt")
    requirements = read("requirements.txt")
    if 'py2app' not in sys.argv:
        setup(
            author = name,
            author_email = email,
            name=package,
            packages=[package],
            package_data={
                package: [f"logo/logo_white.png", f"logo/logo_black.png"],
            },
            entry_points={
                "console_scripts": [
                    f"macos-{source_page}-overlay = macos_{source_page}_overlay:main",
                ],
            },
            include_package_data=True,
            install_requires=requirements,
            version=version,
            url = 'https://github.com/{git_username}/{package}'.format(
                git_username=git_username, package=package),
            download_url = 'https://github.com/{git_username}/{package}/archive/{version}.tar.gz'.format(
                git_username=git_username, package=package, version=version),
            description = description,
            keywords = keywords,
            python_requires = '>=3.10',
            license='MIT',
            classifiers=classifiers
        )
    elif 'py2app' in sys.argv:
        setup(
            app=[f'run_{source_page}.py'],
            options={
                'py2app': {
                    'iconfile': f'{package}/logo/icon.icns',
                    'plist': {
                        'CFBundleName': package_name,
                        'CFBundleIdentifier': f'com.github-{git_username}.macos{source_page}overlay',
                        'LSUIElement': True,
                        'NSMicrophoneUsageDescription': 'Microphone access is needed for voice mode features.',
                        'NSInputMonitoringUsageDescription': 'Needed to listen for your chosen keyboard trigger to show/hide the overlay.',
                    },
                    'includes': ['objc', 'AppKit', 'WebKit', 'Quartz', 'Foundation', 'ApplicationServices'],
                    'excludes': ['docutils', 'setuptools', 'pkg_resources', 'importlib_resources'],
                    'packages': [package],
                    'resources': [
                        f"{package}/logo/logo_white.png",
                        f"{package}/logo/logo_black.png"
                    ],
                }
            },
            setup_requires=['py2app'],
        )