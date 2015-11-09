//包含的头文件
#include "tools.h"
#include "findCircleParameter.h"
#include "corrector.h"
#include "imagesStitcher.h"
#include "viewer.h"

//主程度入口点
int main(int argc, char** argv)
{	
	correctParameters params;
	bool isDispCorrectRet = false;
	corrector adjuster;
	vector<Mat> outputs;

	imagesStitcher stitcher;

	bool saveResult = false;

	//读图片到内存中
	if (tools::readImage())
	{
		vector<Mat>& inputs = tools::GetImages();

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

				cout <<endl			
					<< "Correct Image(s) with the same circular region params: " << endl
					<< "radius = " << params.radius << ", center = " << params.center << endl << endl;

#pragma region 图像校正区
				outputs.push_back(
					adjuster.correctImage(params, corrector::correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_HALF_PI,
						isDispCorrectRet)
					);

				for (int i = 1;i < inputs.size();i++)
				{
					source_image = inputs[i];
					params.imgOrg = source_image;

					outputs.push_back(
						adjuster.correctImage(params, corrector::correctMethod::LONG_LAT_MAP_REVERSE_FORWARD,isDispCorrectRet)
						);
				}
			}
		}	
#pragma endregion
	cout << endl
		<<"Start Stitch images" << endl;
#pragma region 图像接接部分

	if (outputs.size() > 1)
	{
		vector<Mat> images1, images2;
		string filenamePath;
		char suffix[MAX_PATH];
		for (int i = 0;i < outputs.size();i++)
		{
			if (saveResult)
			{
				sprintf_s(suffix, "_corrected%d.jpg", i);
				string tmp(suffix);
				filenamePath = tmp;
				imwrite(filenamePath, outputs[i]);
			}

			if (i < outputs.size() - 1)
				images1.push_back(outputs[i]);
			else
				images2.push_back(outputs[i]);
		}
		images2.insert(images2.begin(), stitcher.stitchImages(images1));
		stitcher.stitchImages(images2);
		stitcher.showPanorama();
	}
#pragma endregion
	cout << "Stitch Images completes!" << endl;

#pragma region 浏览全景图像
	Mat panoramaImage = stitcher.getPanorama();
	if (panoramaImage.empty()) return 0;
	viewer panoViewer(panoramaImage);
	panoViewer.showWindow();
#pragma endregion
	return 0;
}