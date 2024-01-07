# Fish-eye-Image-Correction-Code

- Initially, this project was built to provide support for my thesis which titled "Correction of single circular fisheye image".
And It has been published on the `Journal Of Computer Application(ISSN 1001-9081)`. 
Even if not so good, it is the first thesis I wrote by myself. I try my best to do that well.

- When I graduated from Tianjin University, I expanded the project. 
The purpose is to provide the facts for my graduation thesis. 
Its title called `Research of Panoramic Roaming System Based on Fisheye Images`.

- And you can find all these two thesis in this project, under the directory: `paper/`. 
Theory and practice are not always the same. 
The paper just provides a way of thinking, but not all of it. 
That's just my bad thought. So I wish someone can help me to improve this project, or just give me some advice. That's all.

## The basic features of the project:

You can use this program to carry out basic experiments for circular fisheye images:

* Circular Area Parameters Extration.
* Image Correction.
* Stitching corrected images into a panorama.
* navigate the produced panorama.

User experience is not so good, it only has basic functions.

## How to use this project

1. pre-requirements: 
    - required: 
        - [**install g++ compiler**](https://gcc.gnu.org/install/binaries.html)
        - [**install cmake build tool**](https://cmake.org/download/)
    - optional:
        - [**visual studio code**](https://code.visualstudio.com/)

2. clone repo into you local disk as follow: 

    ```bash
    git clone --recurse-submodules https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code.git
    ```
    this repo have three opencv source repos as submoudle, 
    fetch opencv repos may cost some time, 
    if you live in chinese mainland, `github.com` maybe blocked, 
    please notice these problem
3. change working directory into local repo, build successfully and run program:

    ```bash
    cd Fish-eye-Image-Correction-Code/ && ./build.sh && ./run.sh
    ```

    `run.sh` script use the `ImagesForTest/1/*jpg` images as demonstration.

### Basic situation

* this program is build on MacOS, if you use it on Windows/Linux, maybe you should make some changes of configs or scipts.
Windows platform can use the Linux subsystem, so the changes maybe not so much. and you can make it done. If you need some help, just make me know. ;-D

* recently, I have upgraded the opencv version to 4.9.0, add scripts to build opencv dynamic libs automaticlly.

* when the build completed, there will be a program named `navigator` under directory `product/`, and you can use it to explore.

* you can also use visual studio code to build、debug and run the navigator program.

* opencv source code repo has beed added as three git submodules, but this project only use the main repo.
so you can run the `build.sh` in console to build opencv dynamic libs which be generated in local disk under directory `opencv_install/`
This can help me upgrade opencv version easily.

* you can find some circular fisheye images for testing under the directory: `ImagesForTest/`. 
Only first six directory can be processed by this project, every directory contain four circular fisheye images.

* Because the process of images stitching may fail, you can use the parameters in the file `ImagesForTest/valid_params.txt` during the processing of extracting circular area step.

### Sample Processing

OK! Probably like this. Here is a sample processing.

#### The original images
![image1](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/1.JPG)
![image2](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/2.JPG)
![image3](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/3.JPG)
![image4](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/4.JPG)

#### The corrected images
![corrected1](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/corrected0.jpg)
![corrected2](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/corrected1.jpg)
![corrected3](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/corrected2.jpg)
![corrected4](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/corrected3.jpg)

#### The stitched panorama
![panorama](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/panorama.jpg)

#### navigate the panorama
![navigate](https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code/blob/master/resources/navigate.png)

**The project is in developing, so it may be updated sometime when I feel there should be added something. If you have any question, please connect author or fire an issue on this repo. I will be very happy if I know you are interested in this project. ;-D**


## The project directory tree struct is as follow:

```bash
.
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
│   └── valid_params.txt
├── README.md
├── build.sh
├── opencv
│   ├── contrib
│   ├── extra
│   └── main
├── paper
│   ├── 毕业答辩.pptx
│   ├── 处理过程演示视频.mp4
│   ├── 单幅圆形鱼眼图像的校正.pdf
│   └── 鱼眼成像全景漫游系统的研究.docx
├── product
├── program
│   ├── corrector.cpp
│   ├── corrector.h
│   ├── findCircleParameter.cpp
│   ├── findCircleParameter.h
│   ├── globalInclude.h
│   ├── imagesStitcher.cpp
│   ├── imagesStitcher.h
│   ├── main.cpp
│   ├── tools.cpp
│   ├── tools.h
│   ├── viewer.cpp
│   └── viewer.h
├── resources
│   ├── 1.JPG
│   ├── 2.JPG
│   ├── 3.JPG
│   ├── 4.JPG
│   ├── corrected0.jpg
│   ├── corrected1.jpg
│   ├── corrected2.jpg
│   ├── corrected3.jpg
│   ├── navigate.png
│   └── panorama.jpg
├── run.sh
└── setup-vsc.sh

20 directories, 31 files
```