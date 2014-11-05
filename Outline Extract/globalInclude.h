#pragma once

#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <math.h>
#include <sstream>
#include <string>
#include <fstream>

using namespace std;
using namespace cv;

#define PI		(3.1415926535897932384626433832795)

enum CorrectType
{
	Forward,
	//means correct the distorted image by mapping the pixels on the origin image
	//to the longitude-latitude rectified image, there may be some pixels on the
	//rectified image which have no corresponding origin pixel. 
	Reverse,
	//means correct the distorted image by reverse mapping, that is from the rectified 
	//image to the origin distorted image, this method can be sure for that every pixels
	//on the rectified image have its corresponding origin pixel.
};

typedef enum
{
	PERSPECTIVE,	
	STEREOGRAPHIC,	
	EQUIDISTANCE,	
	EQUISOLID,		
	ORTHOGONAL
}camMode;

//#define _DEBUG_
//#define _SHOW_POINTS_
