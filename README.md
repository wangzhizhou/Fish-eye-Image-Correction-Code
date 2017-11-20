# Fish-Eye-Images-Correction-Stitching-Panorama image navigate-Code

- Initially, this project was built to provide support for my thesis which titled “Correction of single circular fisheye image”. And It has been published on the Journal Of Computer Application(ISSN 1001-9081). Even if not so good, it is the first thesis I wrote by myself. I try my best to do that well.

- When I graduated from Tianjin University, I expanded the project. The purpose is to provide the facts for my graduation thesis. Its title called "Research of Panoramic Roaming System Based on Fisheye Images".

- And you can find all these two thesis in this project, under the directory: `\Paper\`. Theory and practice are not always the same. The paper just provides a way of thinking, but not all of it. That's just my bad thought. So I wish someone can help me to improve this project, or just give me some advice. That's all.

## Basic situation

* You can directly run the `navigator.exe` under the directory: `\product\` if you have not installed `Visual Studio` IDE.

* This project is developed by visual studio 2017 and can be opened by vs2017 or later version. Your computer system should be windows 10 which can install the IDE.

* The OpenCV 3.3.0(opencv-vc14-x64-release) has been included in this project, and you do not need to configure the OpenCV development environment, just checkout the project to you local repo, and use your IDE(vs2017 or later) to open it, then click F5 to build and run it. 

* I have defined some user marcos in the `OpenCV_Release_x64.props` and `OpenCV_Debug_x64.props` to simplify the process of configuring the opencv dlls dependencies.

* The OpenCV related headers and libs has been included in this project, and the dlls are also added in the directory of execute file(in directory: `\product\`). So, it just work!

**Note**: Started from Opencv3.0, the `opencv dlls` had been merge into a large one dll file, and that large file can not been pushed onto GitHub repo directly, because GitHub limit single file's size less than 100MB, so I used the git extension named `Git Large file Storage`, but there is some problem from Chinese Great Wall firewall if you work in China. So, maybe you should fire up a VPN Proxy to download the entire project, or you can mannually download the Opencv 3.3.0 library and overwrite the project's corresponding files(mainly locate in directory: `opencv330vc14x64release/`). 


**The project is in developing, so it may be updated sometime when I feel there should be added something. If you have any question, please connect author or fire an issue on this repo. I will be very happy if I know you are interested in this project. ;-D**


## The basic function of the project:

You can use this program to carry out basic experiments for circular fisheye images:

* Circular Area Parameters Extration.
* Image Correction.
* Stitching corrected images into a panorama.
* navigate the produced panorama.

Experience is not so good, it only has basic functions.

## How to use this project

- Now, this project had been updated using `Opencv3.3.0` library, if you want to check the project that use the opencv 2.4.8 version, you can download the release v1.0 version to get it.

Firstly, you should clone this repo to your computer by using `git` related commands or just download the `zip` released version provided by GitHub.

If you don't want to clone the entire repo, you can clone the latest commit in this project with the command listed as follow:

> `git clone --depth=1 https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code.git`

Then, open the `*.sln` file with your visual studio 2017 or later version.

After open the Solution, make sure the project configruation is `Debug|x64` or `Release|x64`, and press the Key `F5` to build and run this project. 

You can find some circular fisheye images for testing under the directory: `\ImagesForTest\`. Only first six directory can be processed by this project, every directory contain four circular fisheye images.

Because the process of images stitching may fail, you can use the parameters in the file `\ImagesForTest\有效参数.txt` during the processing of extracting circular area step.

OK! Probably like this. Here is a sample processing.

## Sample Processing

#### The original images
![image1](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/1.JPG)
![image2](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/2.JPG)
![image3](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/3.JPG)
![image4](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/4.JPG)

#### The corrected images
![corrected1](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/corrected0.jpg)
![corrected2](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/corrected1.jpg)
![corrected3](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/corrected2.jpg)
![corrected4](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/corrected3.jpg)

#### The stitched panorama
![panorama](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/panorama.jpg)

#### navigate the panorama
![navigate](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/readme_resource/navigate.jpg)

## The project directory tree struct is as follow:
```
FISH-EYE IMAGE CALIBRATION
├── ImagesForTest
│   ├── 1
│   ├── 2
│   ├── 3
│   ├── 4
│   ├── 5
│   ├── 6
│   ├── 7
│   ├── 8
│   ├── 9
│   ├── other
│   └── 有效参数.txt
├── OpenCV_Debug_x64.props
├── OpenCV_Release_x64.props
├── Paper
│   ├── 毕业答辩.pptx
│   ├── 处理过程演示视频.mp4
│   ├── 单幅圆形鱼眼图像的校正.pdf
│   └── 鱼眼成像全景漫游系统的研究.docx
├── README.md
├── navigator
│   ├── corrector.cpp
│   ├── corrector.h
│   ├── findCircleParameter.cpp
│   ├── findCircleParameter.h
│   ├── globalInclude.h
│   ├── imagesStitcher.cpp
│   ├── imagesStitcher.h
│   ├── main.cpp
│   ├── navigator.vcxproj
│   ├── navigator.vcxproj.filters
│   ├── navigator.vcxproj.user
│   ├── tools.cpp
│   ├── tools.h
│   ├── viewer.cpp
│   └── viewer.h
├── navigator.sln
├── opencv330vc14x64release
│   ├── bin
│   ├── include
│   └── lib
├── product
│   ├── navigator.exe
│   └── opencv_world330.dll
└── readme_resource
    ├── 1.JPG
    ├── 2.JPG
    ├── 3.JPG
    ├── 4.JPG
    ├── corrected0.jpg
    ├── corrected1.jpg
    ├── corrected2.jpg
    ├── corrected3.jpg
    ├── navigate.jpg
    └── panorama.jpg

19 directories, 34 files
```

<video src="./Paper/处理过程演示视频.mp4">


