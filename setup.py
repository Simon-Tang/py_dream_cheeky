from setuptools import setup, find_packages

setup(
    name='PyDreamCheeky',
    version='1.0.0b2',
    url='https://github.com/Simon-Tang/py_dream_cheeky',
    license='Unlicense',
    author='Simon Tang',
    author_email='simontang@live.ca',
    description='A convenient Python driver for Dream Cheeky\'s Big Red Button',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Topic :: System :: Hardware :: Hardware Drivers'
    ],
    keywords='dream cheeky big red button usb driver',
    packages=find_packages(),
    install_requires=['pyusb'],

)
