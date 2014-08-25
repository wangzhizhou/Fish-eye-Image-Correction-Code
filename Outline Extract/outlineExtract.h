#pragma once

#include "globalInclude.h"

void ScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold=20);
void HoughCircleMethod(Mat imgOrg, Point2i& center, int radius);
