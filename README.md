# Python waveform parser
A python-based waveform (wbf) parser for parallel e-paper displays. 

⚠️ This is highly experimental, but it seems to work for the most part.

⚠️ Unlike most repos, this repo does not have a license as the aim of this repo is to understand the waveform format and possibly develop converters from one file format to another. 

You are allowed to use this code for private purposes only as long as you publish any progress you have made back to me via a pull request. The recommended approach is to clone the repo, test and develop this code and create a PR with the improvements.

To use the parser, you will need a .wbf file as these files are often restricted and distributing them may be a problem.


## Waveform file
A waveform file is basically a .wbf file, not to be confused with the audio format having the same extension and allows driving parallel e-paper displays. 
Little to none is known about this file format, even getting your hands on one is pretty difficult. 
Without a proper converter, it's impossible to make any sense of the data when opening with a normal text-viewer since it's not encoded in utf-8. I was only able to find a handful of parsers and most of them either didn't work, required installation of more software or compiling the code on special hardware. In short, almost no-one has attempted to write a parser in python, which makes the code much more readable, maintainable and easy to use. 

The reason these files are required in the first place for rendering on e-paper is that unlike LCDs, where pixels can be individually controlled with high-speeds, e-paper displays apply positive and negative voltage to flip small spherical pigments dispersed in oil. Although there are only black and white particles available in a "pixel" of parallel e-paper displays, it is possible to get 16 grayscales. That works by applying a series of the supported voltages for a very short time, causing some of the white and some of the black spheres to reach the surface, where they become visible to the eye and appear gray. Depending on which voltage is applied for which duration in which sequence, it is possible to experiment with the grayscale levels. To make things even more complex, the initial grayscale of the pixel to be changed needs to be known and the new state needa to be remembered. A darker pixel will behave differently than a lighter pixel even with the same voltages applied.

You can therefore imagine a waveform as a 3D block of 16x16 grayscales, since we can jump from any of the 16 grayscales to any other grayscale. The third dimension would then be the actual voltages that need to be applied.


Below is a small breakdown of how this file is made up:
```txt
HEADER...
TEMP-RANGE-1
    ...waveform-for-mode-1...
    ...waveform-for-mode-2...
    ...waveform-for-mode-3...
    ...waveform-for-mode-4...
TEMP-RANGE-2
    ....waveform-for-mode-1...
    ...waveform-for-mode-2...
    ...waveform-for-mode-3...
    ...waveform-for-mode-4...
TEMP-RANGE-3
    ....waveform-for-mode-1...
    ...waveform-for-mode-2...
    ...waveform-for-mode-3...
    ...waveform-for-mode-4...
TEMP-RANGE-4
    ....waveform-for-mode-1...
    ...waveform-for-mode-2...
    ...waveform-for-mode-3...
    ...waveform-for-mode-4...
....
```

Extracting the waveform is already possible with this parser, but I have yet to make any sense out of a waveform itself. For example, a waveform may look like this:
```py
[0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x00, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0x00, 0xFF, 0x01, 0xB0, 0xB0, 0x70, 0x40, 0x00, 0x00]
```

The idea is to be able to convert the waveform into a more usable format, e.g. JSON or CSV, without requiring an intermediate format.

## Usage:
Download the parser, then scroll down this section at the very bottom:
```py
if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	filepath = "waveform.wbf"

	parser = WaveFormParser(filepath)
	waveforms = parser.waveforms
	pprint(waveforms, sort_dicts=False, width=200, compact=True)
	print("completed")
```
Change `filepath = "waveform.wbf"` to the full filepath of your wbf file. Then execute the file with python, `python3 wbf-parser.py`

Although it should display quite a bit of info, the parser has even more potential when used in combination with an IDE or at least something which supports a debugger. 






