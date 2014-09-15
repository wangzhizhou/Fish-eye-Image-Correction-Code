#include "globalInclude.h"

#include "outlineExtract.h"
#include "latitudeCorrection.h"
#include "panoramaExpansion.h"


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

int N_slider = 5;
int threshold_slider = 40;

Mat imgOrg;
const int N_max = 15;
const int threshold_max = 255;

extern const char window_name[] = "Outline Extraction";

Point2i center;
int radius = 0;

void On_N_trackbar(int, void*)
{
	cout << endl;
	cout << "N_Slider"<<N_slider << endl;
	cout << "Threshold_Slider" << threshold_slider << endl;
	revisedScanLineMethod(imgOrg, center, radius, threshold_slider, N_slider);
}

void On_threshold_trackbar(int, void*)
{
	cout << endl;
	cout << "N_Slider: " << N_slider << endl;
	cout << "Threshold_Slider: " << threshold_slider << endl;
	revisedScanLineMethod(imgOrg, center, radius, threshold_slider, N_slider);
}

int main(int argc, char** argv)
{
	if (argc < 2)
	{
		Usage();
		return -1;
	}

	imgOrg = imread(argv[1], CV_LOAD_IMAGE_COLOR);
	if (!imgOrg.data)
	{
		cout << "Failed to read in a image." << endl;
		return -1;
	}

	namedWindow(window_name, CV_WINDOW_AUTOSIZE);

	const char N_trackbar_name[]="N (0-15)";
	const char Threshold_trackbar_name[] = "Threshold(0-255)";

	createTrackbar(N_trackbar_name, window_name, &N_slider, N_max, On_N_trackbar);
	createTrackbar(Threshold_trackbar_name, window_name, &threshold_slider, threshold_max, On_threshold_trackbar);

	On_N_trackbar(N_slider,0);
	On_threshold_trackbar(threshold_slider,0);
	waitKey();

	//latitudeCorrection(imgOrg.clone(), center, radius,  PI*3/4);
	// panoramaExpansion(imgOrg,  center,  radius);

	







	/*Mat chat(256, 256, CV_8U);
	vector<Point> datum;
	int limit = max(imgOrg.size().width, imgOrg.size().height);
	for (int k = 1; k <= 255; k+=20)
	{
		revisedScanLineMethod(imgOrg, center, radius, k);
		radius = 256 - 256 * radius / limit;
		datum.push_back(Point(k, radius));
	}
	polylines(chat, datum, false, Scalar(255, 255, 255), 2);
	imshow("char", chat);*/
	//Extract the center and radius from the origin image
	//imwrite("src.tiff", imgOrg);
	//areaStatisticsMethod(imgOrg, center, radius, 10);
	//HoughCircleMethod(imgOrg, center, radius);
	//ScanLineMethod(imgOrg, center, radius, 120);
	//revisedScanLineMethod(imgOrg, center, radius, 149,5);
	//imshow("imgsrc", imgOrg)
	//Mat img1, img2, img3;
	//for (double r = PI / 20; r <= PI; r += PI / 20)
	//{
	//	img1=panoramaExpansion(imgOrg.clone(), center, radius,r,Forward);
	//	if (img1.data)
	//	{
	//		imshow("ret", img1);
	//		waitKey(10);
	//		
	//	}
	//}

	//User multiple method to correct the distorted image
	//img1=latitudeCorrection( imgOrg,  center,  radius,Forward);
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
//	/// Using Canny¡¯s output as a mask, we display our result
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