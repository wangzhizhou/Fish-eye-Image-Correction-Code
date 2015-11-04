#pragma once
#include <opencv2\opencv.hpp>
#include <iostream>
#include "tools.h"

using namespace std;
using namespace cv;

#define VIEWER_WIDTH (1024)
#define VIEWER_HEIGHT (VIEWER_WIDTH/2)

//const double PI = 3.1415926535897932384626433832795;


class viewer
{
public:
	viewer(Mat inputImg);
	Mat getWindow();
	void showWindow();
	void updataWindow();
	Point3d navigationHV(Point3d orgPt, double angleH, double angleV);
	~viewer() {};
	void refreshWindow();
private:
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