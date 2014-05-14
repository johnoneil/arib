#arib

Japan Association of Radio Industries and Businesses (ARIB) MPEG2 Transport Stream Closed Caption Decoding Tools

##Description
Closed Captions (CCs) are encoded in Japanese MPEG Transport Streams as a separate PES (Packetized Elementary Stream) within the TS. The format of the data within this PES is described by the (Japanese native) ARIB B-24 standard. An English document describing this standard is included in the Arib/docs directory in this repository.

My aim in writing this code was to draw out this Closed Caption data, and make it available for whatever purpose. Currently a small example exists (examples/extract_ccs_from_es.py) which draws out CC character info from a PES (.es) file and dumps it to stdout.

#Installation
Basic installation is now supported, but I only currently recommend installing into a virtualenv as the lib is still only pre-alpha.

That said, installation can now be carried out via pip. I recommend 'editable' (development) install as below.
```
pip install -e git+https://github.com/johnoneil/arib#egg=arib
```

#Example
A simple example that should be easy to run is provided as examples/extract_ccs_from_es.py. This example requies a PES input and simply draws out CC text found in the file, dumping it to the command line. Run it as:
```
./extract_ccs_from_es.py <pes filename>
```
A concrete example of a run follows:
```
joneil@joneilDesktop ~/code/arib $ ./examples/extract_ccs_from_es.py examples/toriko_subs.es
<clear screen>
<clear screen><clear screen>
<clear screen>
<Screen Posiiton to 71,67>＜世はグルメ時代＞
<clear screen>
<Screen Posiiton to 71,65>＜食の探求者<Medium Size Text> <Normal Size Text>美食屋たちは訢
<clear screen>
<Screen Posiiton to 71,65>あまたの食材を追い求める＞
<clear screen><Small Text>
<Screen Posiiton to 76,66><Normal Size Text>＜そして<Medium Size Text> <Normal Size Text>この世の食材の頂点
<Screen Posiiton to 70,66><Small Text>ゴッド<Medium Size Text>
<Screen Posiiton to 70,75><Small Text>ほかく<Normal Size Text>
<Screen Posiiton to 71,65>ＧＯＤの捕獲を目指す訢
<clear screen>
<Screen Posiiton to 71,66>一人の美食屋がいた！＞
<clear screen>
<clear screen>
<Screen Posiiton to 71,64>頰〜
...
```
In the above each line is not timestamped, but you can see the cursor movement info (screen positions in character row/col) text size info, and the on screen CC text data.

Interestingly, you can see how the furigana for certain words (perl or kanji pronunciation guide) is present for many romaji (latin alphabet) and kanji characters. For example the furigana "ゴッド" is positioned as small text above the normal sized text word "ＧＯＤ".

Timestamp info for the for the various text and clear screen commands would have to be drawn out of the .TS packet info. This functionality is not present in this package.

Also note that in the example above, screen positions and other textual information was described using the ARIB control character set.
There is another way in which such info is carried around: via the ARIB control *seqence* character set. Please refer to the ARIB.control_characters.CS class for more info.

An example of inline control sequences carrying text position and other info follows:
```
<CS:"7 S"><CS:"170;30 _"><CS:"620;480 V"><CS:"36;36 W"><CS:"4 X"><CS:"24 Y"><Small Text><CS:"170;389 a">えいえゅゃ<Normal Text><CS:"170;449 a">栄純が<Medium Text><Small Text><CS:"530;449 a">い<Normal Text><CS:"190;509 a">きのぃとはゃなに言っくら訢
```
Refer to the ARIB documentation for descriptions of what these control sequences mean, but some can be summarized here:
* 'S' character indicates time in secons caption is shown (here 7)
* '_' underscore indicates UL corner in pixels of CC area (here at x=170,y=30).
* 'V' indicates the width, height in pixels of the CC area (here 620x480). Note that this is inset inside a stanard screen dimension of 960x540.
* 'W' indicates the height and width of a normal sized character in pixels. Japanese characters tend to be square.
* 'X' is the pixel spacing between characters in CCs.
* 'Y' is the pixel spacing between lines in CCs.
* 'a' Positions the cursor to a screen position in pixels. This is in contrast to the dedicated control character APS (Active Position Set) above which positions the cursor to a particular character *line* and *column*. APS style line and column positions can be translated to pixel positions by using the character width and height, space between characters and lines and the UL position of the CC area (see above).

#Manually drawing a PES from a TS file
I'm currently using TSTools to draw out .es streams (Packetized Elemenatry Streams) from released MPEG TS files.

Parsing .ts streams isn't *too* difficult, but I haven't found a decent python library that I can use yet. Building one will therefore take some time.

Still, here's an example of drawing out an .es from a .ts.

First, use tsinfo to examine the contents of the .ts
```
joneil@joneilDesktop ~/code/arib/analysis $ tsinfo <filename>.ts 
Reading from <filename>.ts
Scanning 1000 TS packets

Packet 452 is PAT
Program list:
    Program 2064 -> PID 0101 (257)

Packet 796 is PMT with PID 0101 (257)
  Program 2064, version 15, PCR PID 0100 (256)
     Program info (15 bytes): 09 04 00 05 e0 31 f6 04 00 0e e0 32 c1 01 84
     Conditional access: id 0005 (5) PID 0031 (49) data (9 bytes): f6 04 00 0e e0 32 c1 01 84
     Descriptor tag f6 (246) (4 bytes): 00 0e e0 32
     Descriptor tag c1 (193) (1 byte): 84
  Program streams:
    PID 0111 ( 273) -> Stream type 02 (  2) H.262/13818-2 video (MPEG-2) or 11172-2 constrained video
        ES info (6 bytes): 52 01 00 c8 01 47
        Descriptor tag 52 ( 82) (1 byte): 00
        Descriptor tag c8 (200) (1 byte): 47
    PID 0112 ( 274) -> Stream type 0f ( 15) 13818-7 Audio with ADTS transport syntax
        ES info (3 bytes): 52 01 10
        Descriptor tag 52 ( 82) (1 byte): 10
    PID 0114 ( 276) -> Stream type 06 (  6) H.222.0/13818-1 PES private data (maybe Dolby/AC-3 in DVB)
        ES info (8 bytes): 52 01 30 fd 03 00 08 3d
        Descriptor tag 52 ( 82) (1 byte): 30
        Descriptor tag fd (253) (3 bytes): 00 08 3d
    PID 0115 ( 277) -> Stream type 06 (  6) H.222.0/13818-1 PES private data (maybe Dolby/AC-3 in DVB)
        ES info (20 bytes): 52 01 38 09 04 00 05 ff ff f6 04 00 0e ff ff fd 03 00 08 3c
...
```
I recognize the PID 276, (stream type 6) as the PES private CC data. That seems to be typical.
Note that sometimes an adequate PAT (Program allocation table) may not be within the first 1000 packets of the .TS, so you might have to run tsinfo with an additional argument (look through more packets for a PAT).
```
tsinfo -max 20000 <filename>.ts
```

Then use ts2es to draw out the ES
```
ts2es -pid 276 <input>.ts <output>.es
```
##Status
First, this project is currenly only a prototype (proof of concept). Much more work remains to make it a usable library.

That said, this project currently operates on MPEG PES streams. These need to be separately drawn from .TS files via some other applicaiton. I'm currently using the TSTools 'ts2es' tool to do this.

The basic ARIB decoder turns this PES (.es file) into an array of objects that contain info regarding things like characters on the screen, text positions and sizes and colors. These objects need a formatter to be written to turn them into whatever you want (extracted text, for example).

Some areas have not bee implemented (yet?)
* There is no current Gaiji support (i.e. custom Arib characters outside the normal shift-jis encoding table).
* DRCS characters (custom characters described as simple bitmaps in the stream data) are detected, but not parsed.
* Many other areas of the ARIB B-24 standard (such as  Mosaic image info) are not implemented.
* ~~Encoding is still weakly handled. Does not follow the best practice of "decode early, encode late" therefore many utf-8 encoding exceptions are likely.~~

