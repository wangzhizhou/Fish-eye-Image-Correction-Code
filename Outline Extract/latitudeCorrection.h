//Written by WangZhizhou in TianJin University for the small paper and the interest.
#pragma once

#include "globalInclude.h"

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

/*

*/
Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, CorrectType type = Reverse, double camerFieldAngle = PI*11/15);
