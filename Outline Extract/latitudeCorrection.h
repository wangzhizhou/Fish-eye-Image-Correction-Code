//Written by WangZhizhou in TianJin University for the small paper and the interest.
#pragma once

#include "globalInclude.h"

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, double camerFieldAngle = PI * 11 / 15, CorrectType type = Reverse );
Mat cylinderCorrection(Mat imgOrg, Point2i center, int radius);