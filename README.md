# Fish-eye-Image-Correction-Code

- Initially, this project was built to provide support for my thesis which titled “Correction of single circular fisheye image”. And It has been published on the Journal Of Computer Application(ISSN 1001-9081). Even if not so good, it is the first thesis I wrote by myself. I try my best to do that well.

- When I graduated from Tianjin University, I expanded the project. The purpose is to provide the facts for my graduation thesis. Its title called "Research of Panoramic Roaming System Based on Fisheye Images".

- And you can find all these two thesis in this project, under the directory: `paper`. Theory and practice are not always the same. The paper just provides a way of thinking, but not all of it. That's just my bad thought. So I wish someone can help me to improve this project, or just give me some advice. That's all.

## Basic situation

* You can directly run the executable program under the directory: `product` if you just want to have a look at the result.

* This project is developed by visual studio code.

* The opencv source code repo has beed added as three git submodules, so you can enter the `opencv` directory to build static libs. This can help me upgrade opencv version easily.

* I have defined some user marcos in the `OpenCV_Release_x64.props` and `OpenCV_Debug_x64.props` to simplify the process of configuring the opencv dlls dependencies.

**The project is in developing, so it may be updated sometime when I feel there should be added something. If you have any question, please connect author or fire an issue on this repo. I will be very happy if I know you are interested in this project. ;-D**


## The basic function of the project:

You can use this program to carry out basic experiments for circular fisheye images:

* Circular Area Parameters Extration.
* Image Correction.
* Stitching corrected images into a panorama.
* navigate the produced panorama.

User experience is not so good, it only has basic functions.

## How to use this project

> pre-requirements: you should install `g++` compiler and `cmake` cli build tool

You can clone this repo into your local disk to play around as follow:

```bash
git clone --recurse-submodules https://github.com/wangzhizhou/Fish-eye-Image-Correction-Code.git && cd Fish-eye-Image-Correction-Code && ./build.sh && ./run.sh
```

You can find some circular fisheye images for testing under the directory: `ImagesForTest`. Only first six directory can be processed by this project, every directory contain four circular fisheye images.

Because the process of images stitching may fail, you can use the parameters in the file `ImagesForTest/valid_params.txt` during the processing of extracting circular area step.

OK! Probably like this. Here is a sample processing.

## Sample Processing

#### The original images
![image1](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/1.JPG)
![image2](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/2.JPG)
![image3](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/3.JPG)
![image4](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/4.JPG)

#### The corrected images
![corrected1](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/corrected0.jpg)
![corrected2](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/corrected1.jpg)
![corrected3](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/corrected2.jpg)
![corrected4](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/corrected3.jpg)

#### The stitched panorama
![panorama](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/panorama.jpg)

#### navigate the panorama
![navigate](https://github.com/wangzhizhou2014GitHub/Fish-eye-Image-Correction-Code/blob/master/resources/navigate.jpg)

## The project directory tree struct is as follow:

** TODO: add a directory tree when completed! **

```bash
tree -L 2 .
```