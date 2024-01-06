#pragma once
#include "globalInclude.h"
#include <Windows.h>

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

