#pragma once
#include "globalInclude.h"
#define MAX_PATH 260

class tools
{
public:
	static bool readImage();
	static bool GetFilePathToProcess();
	static void Tip(string message="");
	static vector<Mat>& GetImages();
private:
	tools() {}
	~tools() {}
private:	
	static vector<string> fileNames;
	static vector<Mat> images;
	
};

