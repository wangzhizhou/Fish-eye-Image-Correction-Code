#pragma once

#include "globalInclude.h"

void areaStatisticsMethod(Mat imgOrg, Point2i& center, int& radius, int threshold=20);
void ScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold = 20, Point offsetCenter=Point(0,0), int adjustRadius=0);
void HoughCircleMethod(Mat imgOrg, Point2i& center, int &radius);

void revisedScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold = 20, int N = 10);
bool CircleFitByKasa(vector<Point> validPoints, Point& center, int& radius);
