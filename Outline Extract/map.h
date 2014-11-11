#pragma once
#include "globalInclude.h"

#define FOV		PI	//定义视场角
void findPoints(Point2i center, int radius,std::vector<cv::Point> &points, camMode projMode = ORTHOGONAL);