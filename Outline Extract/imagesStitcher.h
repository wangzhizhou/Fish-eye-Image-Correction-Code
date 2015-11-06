#pragma once
#include "tools.h"

class imagesStitcher
{
private: 
	Mat panorama;	
	string panorama_winname;

public:
	imagesStitcher();
	~imagesStitcher();
	Mat stitchImages(vector<Mat>& images);
	void showPanorama();
	static void onMouse(int event, int x, int y, int, void* args);
};