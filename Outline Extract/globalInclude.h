#pragma once

#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <math.h>

using namespace std;
using namespace cv;

#define PI		(3.1415926535897932384626433832795)

#define _DEBUG_
#define _VIEW_FIELD_

#define	WIDTH	600
#define HEIGHT	WIDTH

#ifndef _VIEW_FIELD_
	#define CAMER_VIEW_FIELD	(PI)
#else
	#define CAMER_VIEW_FIELD	(PI*2/3)
#endif

