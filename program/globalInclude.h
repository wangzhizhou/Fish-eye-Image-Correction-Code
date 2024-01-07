#pragma once
#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/highgui/highgui_c.h>
#include <opencv2/stitching/warpers.hpp>
#include <math.h>
#include <sstream>
#include <string>
#include <fstream>

using namespace std;
using namespace cv;

typedef cv::Mat			Mat;
typedef cv::Point		Point;
typedef cv::Point2i		Point2i;
typedef cv::Size		Size;
typedef cv::Vec3b		Vec3b;
typedef cv::Scalar		Scalar;
typedef cv::Rect		Rect;
typedef cv::Point3f		Point3f;
typedef cv::Point3i		Point3i;
typedef cv::Stitcher	Stitcher;


const double  PI = 3.1415926535897932384626433832795;
const double  LIMIT = 1e-4;

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
	STEREOGRAPHIC,	
	EQUIDISTANCE,	
	EQUISOLID,		
	ORTHOGONAL
}camMode;

typedef enum
{
	PERSPECTIVE,
	LATITUDE_LONGTITUDE,
}distMapMode;

//#define _DEBUG_
//#define _SHOW_POINTS_
