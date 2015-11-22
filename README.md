# Fish-Eye-Images-Correction-Stitching-Panorama image navigate-Code

- Initially, this project was built to provide support for my thesis which titled “Correction of single circular fisheye image”. 
And It has been published on the Journal Of Computer Application(ISSN 1001-9081). Even if not so good, it is the first thesis I wrote by myself. I try my best to do that well.

- When I graduated from Tianjin University, I expanded the project. The purpose is to provide the facts for my graduation thesis. Its title called "Research of Panoramic Roaming System Based on Fisheye Images".

- And you can find all these two thesis in this project, under the directory: `\Paper\`. Theory and practice are not always the same. The paper just provides a way of thinking, but not all of it. That's just my bad thought. So I wish someone can help me to improve this project, or just give me some advice. That's all.

## Basic situation

* You can directly run the `navigator.exe` under the directory: `\product\` if you have not installed `Visual Studio` IDE.

* This project is developed by visual studio 2015 and can be opened by vs2015 or later version. You computer system should be windows 8.1/10 which can install the IDE.

* The OpenCV 2.4.8 is used in this code, and you do not't need to configure the OpenCV development environment, just checkout the project to you local repo, and use you IDE(vs2015 or later) to open it, then click F5 to build and run it.

* If you found the program can been build successfully, but need some dlls to run. You should open the `project property page` and clike the `Debug` label in the left column, then change the `Work Directory` value(in the right column) to `$(SolutionDir)opencv248vc12x86release\bin`, and re-run the built project.

* The OpenCV related headers and libs has been included in this project, and the dlls are also added in the directory of execute file. So, it just work!

* And the project is in developing, so it may be updated sometime when I feel there should be added something.

## This basic function of the project:
You can use this program to carry out basic experiments for circular fisheye images:

* Circular Area Parameters Extration.
* Image Correction.
* Stitching corrected images into a panorama.
* navigate the produced panorama.

Effect is not so good, it only has basic functions.

## How to use this project
Firstly, you should clone this repo to you computer by using `git` related commands or just download the `zip` version provide by GitHub.

If you don't want to clone the entire repo, you can clone the latest commit in this project with the command listed follow:

> `git clone repo-site --depth=1`

Then, open the `*.sln` file with your visual studio 2015 or later version.

After open the Solution, make sure the project configruation is `Release|Win32|X86`, and press the Key `F5` to build and run this project. 

You can find some circular fisheye images for test under the directory: `\ImagesForTest\`. Only first six directory can be processed by this project, every directory contain four circular fisheye images.

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
├─ImagesForTest
│  ├─1
│  ├─2
│  ├─3
│  ├─4
│  ├─5
│  ├─6
│  ├─7
│  ├─8
│  ├─9
│  └─other
├─navigator
│  └─Release
│      └─navigator.tlog
├─opencv248vc12x86release
│  ├─bin
│  ├─include
│  │  ├─opencv
│  │  └─opencv2
│  │      ├─calib3d
│  │      ├─contrib
│  │      ├─core
│  │      ├─features2d
│  │      ├─flann
│  │      ├─gpu
│  │      │  └─device
│  │      │      └─detail
│  │      ├─highgui
│  │      ├─imgproc
│  │      ├─legacy
│  │      ├─ml
│  │      ├─nonfree
│  │      ├─objdetect
│  │      ├─ocl
│  │      ├─photo
│  │      ├─stitching
│  │      │  └─detail
│  │      ├─superres
│  │      ├─ts
│  │      ├─video
│  │      └─videostab
│  └─lib
├─Paper
├─product
└─readme_resource
```




