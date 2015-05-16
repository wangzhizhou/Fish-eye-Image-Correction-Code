//包含的头文件
#include "tools.h"
#include "findCircleParameter.h"

#include "latitudeCorrection.h"
#include "cylinderCorrection.h"
#include "panoramaExpansion.h"

//主程度入口点
int main(int argc, char** argv)
{
	//读图片到内存中
	if (tools::readImage())
	{
		if (findCircleParameter::init(tools::GetImage()))
		{
			findCircleParameter::findCircle();

			if (IDOK == MessageBox(NULL, "Would you want to check the FOV of fish-eye lens is valid?", "Check FOV", IDOK))
			{
				findCircleParameter::checkVarify();
			}
			else
				cout << "You have not choose to check the FOV" << endl;
		}
	}
	 
//
//	/*这一部分只针对鱼眼像片是朝向天空和大地拍摄的图像进行的校正
//		Mat img1, img2, img3;
//	for (double r = PI / 20; r <= PI; r += PI / 20)
//	{
//		img1=panoramaExpansion(imgOrg.clone(), center, radius,r,Forward);
//		if (img1.data)
//		{
//			imshow("ret", img1);
//			waitKey(10);			
//		}
//	}
//	*/
//
//
//
//	//下一步进行鱼眼图像的校正
//	Mat ret=latitudeCorrection4(imgOrg, center, radius,/*PI*5/6*/PI/180*90,PI/180*90);
//	imwrite("left.jpg", ret);
//	destroyWindow(window_name);
////	destroyWindow(winname);
//	namedWindow("ret", CV_WINDOW_NORMAL);
//	resizeWindow("ret", 512, 512);
//	imshow("ret", ret);
//
//
//	namedWindow("org", CV_WINDOW_NORMAL);
//	resizeWindow("org", 512, 512);
//	imshow("org", imgOrg);
//	Mat ret1 = latitudeCorrection5(imgOrg, center, radius,PI/180*90,PI/180*90);//如何让两个方向的调整互不影响
//	imshow("org", ret1);	 
//	imwrite("forwardMap.jpg",ret1);
//	/*
//		//使用多种方法来校正鱼眼图像，下面是经纬校正法
//	//Mat img1, img2, img3;
//	//img1=latitudeCorrection( imgOrg.clone(),  center,  radius,PI*17/20);
//	//imshow("image1", img1);
//	//for (double r = PI / 20; r <= PI; r += PI / 20)
//	//{
//	//	img2 = latitudeCorrection(imgOrg.clone(), center, radius,  r);
//	//	//img2 = latitudeCorrection(imgOrg.clone(), center, radius, r,Forward);
//	//	if (img2.data)
//	//	{
//	//		imshow("img2", img2);
//	//		waitKey(5);
//	//	}
//	//	else
//	//	{
//	//		cout << "Failed to rectified!" << endl;
//	//	}
//	//}
//
//	*/
//	
//
//	//漫游算法雏形
//	//std::ostringstream fileName;
//	//double stepAng = PI / 6;
//	//int Number = 0;
//	//for (double i = -PI / 2; i < PI / 2; i += stepAng)
//	//{
//	//	for (double j = -PI / 2; j < PI / 2; j += stepAng)
//	//	{
//	//		Mat ret1 = latitudeCorrection3(imgOrg, center, radius, PERSPECTIVE, i, j);
//	//		////imshow("org", ret1);
//	//		fileName << "stitch\\" << ++Number << ".jpg";
//	//		imwrite(fileName.str().c_str(), ret1);
//	//		//std::cout << fileName.str() << endl;
//	//		fileName.str("");
//	//	}
//	//}
//
//	
//	waitKey();
	return 0;
}



//#include "opencv2/imgproc/imgproc.hpp"
//#include "opencv2/highgui/highgui.hpp"
//#include <stdlib.h>
//#include <stdio.h>
//using namespace cv;
///// Global variables
//Mat src, src_gray;
//Mat dst, detected_edges;
//int edgeThresh = 1;
//int lowThreshold;
//int const max_lowThreshold = 100;
//int ratio = 3;
//int kernel_size = 3;
//char* window_name = "Edge Map";
///**
//* @function CannyThreshold
//* @brief Trackbar callback - Canny thresholds input with a ratio 1:3
//*/
//void CannyThreshold(int, void*)
//{
//	/// Reduce noise with a kernel 3x3
//	blur(src_gray, detected_edges, Size(3, 3));
//	/// Canny detector
//	Canny(detected_edges, detected_edges, lowThreshold, lowThreshold*ratio, kernel_size);
//	/// Using Canny’s output as a mask, we display our result
//	dst = Scalar::all(0);
//	src.copyTo(dst, detected_edges);
//	cvtColor(dst, dst, CV_BGR2GRAY);
//	cv::threshold(dst, dst, 60, 255, CV_THRESH_BINARY);
//	imshow(window_name, dst);
//	
//	imwrite("Hough_edge.tiff", dst);
//}
///** @function main */
//int main(int argc, char** argv)
//{
//	/// Load an image
//	src = imread(argv[1]);
//	if (!src.data)
//	{
//		return -1;
//	}
//	/// Create a matrix of the same type and size as src (for dst)
//	dst.create(src.size(), src.type());
//	/// Convert the image to grayscale
//		cvtColor(src, src_gray, CV_BGR2GRAY);
//	/// Create a window
//	namedWindow(window_name, CV_WINDOW_AUTOSIZE);
//	/// Create a Trackbar for user to enter threshold
//	createTrackbar("Min Threshold:", window_name, &lowThreshold, max_lowThreshold, CannyThreshold);
//	/// Show the image
//	CannyThreshold(0, 0);
//	/// Wait until user exit program by pressing a key
//	waitKey(0);
//	return 0;
//}