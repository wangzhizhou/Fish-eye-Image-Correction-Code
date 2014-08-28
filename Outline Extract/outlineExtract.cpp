#include "outlineExtract.h"

void ScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold,Point offsetCenter, int adjustRadius)
{
	Mat src,gray;
	src = imgOrg.clone();
	cvtColor(src, gray, CV_BGR2GRAY);

	//GaussianBlur(gray, gray, Size(9, 9), 2, 2);

	int left, right, top, bottom;


	double minVal, maxVal;
	Point2i minLoc, maxLoc;

	uchar count = 0;
	for (int i = 0; i < gray.rows; i++)
	{
		minMaxLoc(gray.row(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			top = i;
			count++;
			break;
		}
	}
	for (int i = gray.rows-1; i >=0; i--)
	{
		minMaxLoc(gray.row(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			bottom = i;
			count++;
			break;
		}
	}
	for (int i = 0; i < gray.cols; i++)
	{
		minMaxLoc(gray.col(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			left = i;
			count++;
			break;
		}
	}
	for (int i = gray.cols-1; i >=0; i--)
	{
		minMaxLoc(gray.col(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			right = i;
			count++;
			break;
		}
	}
	if (4 != count)
	{
		cout << "The ScanLine Method Failed!" << endl
			<< "Tip: " << endl
			<< "\tyou can try to adjust " << endl
			<< "\tthe value of threshold to make it work." << endl
			<< "\tcurrent value of threshold is: " << threshold << endl;
		return;
	}
	//rectangle(src, Point(left, top), Point(right, bottom), Scalar(0, 0, 255),2);
	
	center.x =(right + left) / 2+offsetCenter.x;
	center.y =(top + bottom) / 2+offsetCenter.y;

	double radius_max = max(right - left, bottom - top) / 2;
	double radius_min = min(right - left, bottom - top) / 2;
	double radius_avg = (radius_max + radius_min) / 2;

	radius = radius_max+adjustRadius;

#ifdef _DEBUG_
	cout << "Use the ScanLine Method:" << endl
		 << "\tThe center is (" << center.x << ", " 
		 << center.y << ")" << endl
		 << "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255),2);
	circle(src, center, 3, Scalar(0, 255, 255), -1);

	namedWindow("ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	imshow("ScanLine Method Result", src);
	waitKey();
#endif

}

void HoughCircleMethod(Mat imgOrg, Point2i& center, double radius)
{
	Mat src,gray;
	src = imgOrg.clone();

	cvtColor(src, gray, CV_BGR2GRAY);
	GaussianBlur(gray, gray, Size(9, 9), 2, 2);

	vector<Vec3f> circles;
	HoughCircles(gray, circles, CV_HOUGH_GRADIENT, 1, gray.rows / 8, 200, 100, 0, 0);

	for (size_t i = 0; i < circles.size(); i++)
	{
		Point center(cvRound(circles[i][0]), cvRound(circles[i][1]));
		int radius = cvRound(circles[i][2]);
		// circle center
		circle(src, center, 3, Scalar(0, 255, 0), -1, 8, 0);
		// circle outline
		circle(src, center, radius, Scalar(0, 0, 255), 2, 8, 0);
	}

	/// Show your results
	center.x =circles[0][0];
	center.y =circles[0][1];
	radius = circles[0][2];

#ifdef _DEBUG_
	cout << "Use the HoughCircle Method:" << endl 
		 << "\tThe center is (" << center.x << ", " 
		 << center.y << ")" << endl
		 << "\tThe radius is " << radius << endl;

	namedWindow("Hough Circle Transform Result", CV_WINDOW_AUTOSIZE);
	imshow("Hough Circle Transform Result", src);	
	waitKey(); 
#endif

}

