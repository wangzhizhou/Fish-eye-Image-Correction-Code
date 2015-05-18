#pragma once
#include "globalInclude.h"
#include <Windows.h>

class tools
{
public:
	static bool readImage();
	static bool GetFilePathToProcess();
	static void Tip(string message);
	static Mat GetImage();
	static void DisplayImage(Mat img);
	static void CompareTwoImages(Mat img1, Mat img2);
private:
	tools();
	~tools();
private:
	static string filePathToProcess;
	static Mat image;
	
};

