#pragma once
#include "tools.h"

class imagesStitcher
{
private: 
	vector<Mat> images;
	Mat panorama;
public:
	imagesStitcher(vector<Mat> images);
	Mat stitch();
	~imagesStitcher();
};

