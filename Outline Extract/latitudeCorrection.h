//Written by WangZhizhou in TianJin University for the small paper and the interest.
#pragma once

#include "globalInclude.h"

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, double camerFieldAngle = PI , CorrectType type = Reverse );


Mat latitudeCorrection2(Mat imgOrg, Point2i center, int radius, distMapMode distMap = LATITUDE_LONGTITUDE, double camerFieldAngle = PI,
	camMode camProjMode = EQUIDISTANCE);
