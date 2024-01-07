// 包含的头文件
#include "tools.h"
#include "findCircleParameter.h"
#include "corrector.h"
#include "imagesStitcher.h"
#include "viewer.h"

bool isDispCorrectRet = false;
bool saveResult = false;
bool haveImage = false;

vector<string> imagePaths;

static void help()
{
	printf("This is a navigator based on fisheye images.\n"
		   "\nUsage: navigator [options] [<image 1 path> <image 2 path> ...]\n"
		   "\nOptions:\n"
		   "     -d     # display the corrected fisheye images.\n"
		   "     -s     # save the result of image process into files.\n"
		   "     -h     # show the help information.\n");
}
void paserParams(int argc, char **argv)
{
	if (argc > 1)
	{
		for (int i = 1; i < argc; i++)
		{
			if (strcmp(argv[i], "-d") == 0)
				isDispCorrectRet = true;
			else if (strcmp(argv[i], "-s") == 0)
				saveResult = true;
			else if (strcmp(argv[i], "-h") == 0)
			{
				help();
				exit(0);
			}
			else {
				string imagePath = string(argv[i]);
				imagePaths.push_back(imagePath);
			}
		}
	}
	if (imagePaths.empty())
	{
		printf("you should enter at least one image to process -_-#\n");
		exit(0);
	}
	else
	{
		cout << endl << "you selected images as follow:" << endl;
		for(int i = 0; i <= imagePaths.size(); i++) {
			cout<<imagePaths[i]<<endl;
		}
	}
}

// 主程度入口点
int main(int argc, char **argv)
{
	paserParams(argc, argv);

	correctParameters params;
	corrector adjuster;
	vector<Mat> outputs;
	imagesStitcher stitcher;

	// 读图片到内存中
	if (tools::readImage(imagePaths))
	{
		vector<Mat> &inputs = tools::GetImages();

		Mat source_image = inputs[0];

		if (findCircleParameter::init(source_image))
		{
			findCircleParameter::findCircle();

#pragma region 校正参数设定区
			params.imgOrg = source_image;
			findCircleParameter::getCircleParatemer(params.center, params.radius);
			params.w_longtitude = PI / 2;
			params.w_latitude = PI / 2;
			params.distMap = LATITUDE_LONGTITUDE;
			params.theta_left = 0;
			params.phi_up = 0;
			params.camerFieldAngle = findCircleParameter::FOV;
			params.camProjMode = EQUIDISTANCE;
			params.typeOfCorrect = Reverse;
#pragma endregion

			cout << endl
				 << "Correct Image(s) with the same circular region params: " << endl
				 << "radius = " << params.radius << ", center = " << params.center << endl
				 << endl;

#pragma region 图像校正区
			corrector::correctMethod method = corrector::correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_HALF_PI;

			outputs.push_back(
				adjuster.correctImage(params, method,
									  isDispCorrectRet));

			for (int i = 1; i < inputs.size(); i++)
			{
				source_image = inputs[i];
				params.imgOrg = source_image;

				outputs.push_back(
					adjuster.correctImage(params, method, isDispCorrectRet));
			}
		}
	}
#pragma endregion

#pragma region 图像接接部分
	vector<Mat> images1, images2;
	string filenamePath;
	char suffix[MAX_PATH];
	for (int i = 0; i < outputs.size(); i++)
	{
		if (saveResult)
		{
			snprintf(suffix, MAX_PATH, "corrected%d.jpg", i);
			string tmp(suffix);
			filenamePath = tmp;
			imwrite(filenamePath, outputs[i]);
		}
		if (i < outputs.size() - 1)
			images1.push_back(outputs[i]);
		else
			images2.push_back(outputs[i]);
	}

	if (outputs.size() > 1)
	{
		cout << endl
			 << "Start Stitch images" << endl;

		Mat tmpRet = stitcher.stitchImages(images1);
		images2.insert(images2.begin(), tmpRet.clone());
		stitcher.stitchImages(images2);
		stitcher.showPanorama();

		cout << "Stitch Images completes!" << endl;
#pragma endregion
#pragma region 浏览全景图像

		Mat panoramaImage = stitcher.getPanorama();

		if (!panoramaImage.empty())
		{
			if (saveResult)
				imwrite("panorama.jpg", panoramaImage);

			viewer panoViewer(panoramaImage);
			panoViewer.showWindow();
		}
#pragma endregion
	}
	return 0;
}