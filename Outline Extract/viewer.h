#pragma once
#include <opencv2\opencv.hpp>
#include <iostream>
#include "tools.h"

using namespace std;
using namespace cv;

#define VIEWER_WIDTH (1024)
#define VIEWER_HEIGHT (VIEWER_WIDTH/2)

class viewer
{
public:
	viewer(Mat inputImg);
	Mat getWindow();
	void showWindow();
	~viewer() {};
private:
	void updataWindow();
	Point3d navigationHV(Point3d orgPt, double angleH, double angleV);
	void refreshWindow();
	static void onMouse(int event, int x, int y, int, void* params);
private:
	Mat paronoma;
	Mat paronomaWithOutline;
	Mat window;
	double angleH;
	double angleV;
	string winname;
	string winname_paronomaWithOutline;
	double distance;
};