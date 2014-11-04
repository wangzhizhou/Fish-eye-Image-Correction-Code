//包含的头文件
#include "globalInclude.h"

#include "outlineExtract.h"
#include "latitudeCorrection.h"
#include "cylinderCorrection.h"
#include "panoramaExpansion.h"
//用法提示
void Usage()
{
	cout << "Usage: extract.exe <image-path> " << endl;
}


/* Best Parameter for images*/
//(2,10) for 1.jpg
//(6,149) for 2.jpg
//(5,20) for 3.jpg
//(5,50) for 4.jpg
//(5,30) for 5.jpg
//(6,40) for 6.jpg
//(6,30) for 7.jpg
//(5,40) for 8.jpg
//(8,16) for 9.jpg
//(5,20) for 10.jpg
//(7,32) for 11.jpg


//滑动块初始值设定
int N_slider = 5;				//变角度线扫描法的角度方向数初值
const int N_max = 15;			//变角度线扫描法的角度方向数最大设定值

int threshold_slider = 40;		//线扫描的阈值
const int threshold_max = 255;	//线扫描阈值最大设定值


extern const char window_name[] = "Outline Extraction";

Mat imgOrg;						//原始图像
Point2i center;					//提取畸变中心，这里设定为鱼眼图像圆形区域的中心
int radius = 0;					//鱼眼图像圆形有效区域的半径

//为确定鱼眼圆形有效区域参数而设置的回调函数，供OpenCV使用
void On_N_trackbar(int, void*)
{
	cout << endl;
	cout << "N_Slider"<<N_slider << endl;
	cout << "Threshold_Slider" << threshold_slider << endl;
	//用变角度线扫描法取求圆形有效区域的圆心和半径的参数
	revisedScanLineMethod(imgOrg, center, radius, threshold_slider, N_slider);
}
void On_threshold_trackbar(int, void*)
{
	cout << endl;
	cout << "N_Slider: " << N_slider << endl;
	cout << "Threshold_Slider: " << threshold_slider << endl;
	//用变角度线扫描法取求圆形有效区域的圆心和半径的参数
	revisedScanLineMethod(imgOrg, center, radius, threshold_slider, N_slider);
}


std::vector<std::vector<cv::Point>> lines;
std::vector<cv::Point> points;

std::string winname = "image";

cv::Mat source;
cv::Mat image;
cv::Mat result;

static void onMouse(int event, int x, int y, int, void* args)
{

	cv::Point pt(x, y);
	switch (event)
	{
	case cv::EVENT_LBUTTONDOWN:
		cv::circle(image, pt, 15, cv::Scalar(0, 255, 0), -1);
		cv::imshow(winname, image);
		points.push_back(pt);
		if (2 == points.size())
		{
			cv::line(image, points[0], points[1], cv::Scalar(0, 255, 255), 3);

			cv::imshow(winname, image);
			lines.push_back(points);
			points.clear();
		}

		break;
	default:
		;
	}
}

//主程度入口点
int main(int argc, char** argv)
{
	//至少要有一幅图像作为输入参数
	if (argc < 2)
	{
		Usage();
		return -1;
	}
	//读图像进入内存
	imgOrg = imread(argv[1], IMREAD_COLOR);
	if (!imgOrg.data)
	{
		cout << "Failed to read in a image." << endl;
		return -1;
	}
	//namedWindow(window_name, CV_WINDOW_NORMAL);
	//resizeWindow(window_name, 512, 612);
	//moveWindow(window_name, 800, 300);
	//const char N_trackbar_name[]="N (0-15)";
	//const char Threshold_trackbar_name[] = "Threshold(0-255)";
	//createTrackbar(N_trackbar_name, window_name, &N_slider, N_max, On_N_trackbar);
	//createTrackbar(Threshold_trackbar_name, window_name, &threshold_slider, threshold_max, On_threshold_trackbar);
	//On_N_trackbar(N_slider,0);
	//On_threshold_trackbar(threshold_slider,0);
	//waitKey();//获得了鱼眼图像圆形有效区域的圆心坐标和半径

	//上面完成了有效区域半径和圆心的的参数提取工作
	center = Point(1097, 1102);
	radius = 1097;	

	image = imgOrg.clone();
	namedWindow(winname, CV_WINDOW_NORMAL);
	resizeWindow(winname, 512, 512);
	moveWindow(winname, 800, 300);
	//circle(image, center, radius, Scalar(0, 0, 255), image.cols / 300);
	//circle(image, center, image.cols/300, Scalar(0, 255, 255), -1);
	imshow(winname, image);
	setMouseCallback(winname, onMouse);
	waitKey();


















	/*这一部分只针对鱼眼像片是朝向天空和大地拍摄的图像进行的校正
		Mat img1, img2, img3;
	for (double r = PI / 20; r <= PI; r += PI / 20)
	{
		img1=panoramaExpansion(imgOrg.clone(), center, radius,r,Forward);
		if (img1.data)
		{
			imshow("ret", img1);
			waitKey(10);			
		}
	}
	*/

	////下一步进行鱼眼图像的校正
	//Mat ret=latitudeCorrection(imgOrg, center, radius);
	//destroyWindow(window_name);

	//namedWindow("ret", CV_WINDOW_NORMAL);
	//resizeWindow("ret", 512, 512);
	//imshow("ret", ret);

	 
	/*
		//使用多种方法来校正鱼眼图像，下面是经纬校正法
	//Mat img1, img2, img3;
	//img1=latitudeCorrection( imgOrg.clone(),  center,  radius,PI*17/20);
	//imshow("image1", img1);
	//for (double r = PI / 20; r <= PI; r += PI / 20)
	//{
	//	img2 = latitudeCorrection(imgOrg.clone(), center, radius,  r);
	//	//img2 = latitudeCorrection(imgOrg.clone(), center, radius, r,Forward);
	//	if (img2.data)
	//	{
	//		imshow("img2", img2);
	//		waitKey(5);
	//	}
	//	else
	//	{
	//		cout << "Failed to rectified!" << endl;
	//	}
	//}

	*/
		
	waitKey();
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