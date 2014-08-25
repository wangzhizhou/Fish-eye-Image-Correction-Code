#pragma once

#include "globalInclude.h"

enum CorrectType
{
	Forward,
	Reverse,
};

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, CorrectType type=Reverse);
