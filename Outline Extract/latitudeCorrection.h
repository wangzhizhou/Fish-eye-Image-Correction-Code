//Written by WangZhizhou in TianJin University for the small paper and the interest.
#pragma once

#include "globalInclude.h"

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, CorrectType type = Reverse, double camerFieldAngle = PI*11/15);
