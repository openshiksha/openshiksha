function PerformanceBreakdownElement(performance_breakdown_element){
	this.date=performance_breakdown_element.date;
	this.topic=performance_breakdown_element.topic;
	this.class_average=performance_breakdown_element.class_average;
	this.student_score=performance_breakdown_element.student_score;
}

function PerformanceBreakdown(performance_breakdown){
	this.subject=performance_breakdown.subject;
    this.subject_teacher=performance_breakdown.subject_teacher;
	this.listing=performance_breakdown.listing;
}

function PerformanceReportElement(performance_report_element){
    this.subject=performance_report_element.subject;
    this.student_average=performance_report_element.student_average;
    this.class_average=performance_report_element.class_average;
}

function PerformanceReport(performance_report){
    this.class_teacher=performance_report.class_teacher;
    this.listing=performance_report.listing;
    
}
 
function Performance(performance){
    this.performance_report=performance.performance_report;
    this.breakdown_listing=performance.breakdown_listing;
}

function SubjectroomPerformanceBreakdownElement(subjectroom_performance_breakdown_element){
    this.date=subjectroom_performance_breakdown_element.date;
    this.topic=subjectroom_performance_breakdown_element.topic;
    this.subjectroom_average= subjectroom_performance_breakdown_element.subjectroom_average;
    this.class_average=subjectroom_performance_breakdown_element.class_average;
}


function SubjectroomPerformanceBreakdown(subjectroom_performance_breakdown){
    this.subject_room= subjectroom_performance_breakdown.subject_room;
    this.subject_teacher=subjectroom_performance_breakdown.subject_teacher;
    this.listing=subjectroom_performance_breakdown.listing;
}

function AssignmentPerformanceElement(assignment_performance_element){
    this.full_name=assignment_performance_element.full_name;
    this.score=assignment_performance_element.score;
}

var mock_assignmentperformancedata1={
    full_name: "Sharang Pai",
    score: 91
}

var mock_assignmentperformancedata2={
    full_name: "Oasis Vali",
    score: 100
}

var mock_assignmentperformancedata3={
    full_name: "Sidhant Pai",
    score: 92
}

var mock_assignmentperformancedata4={
    full_name: "Pujan Parikh",
    score: 82
}

var mock_assignmentperformancedata5={
    full_name: "Hrishikesh Rao",
    score: 77
}

var mock_assignmentperformancedata6={
    full_name: "Abizer Lokhandwala",
    score: 75
}

var mock_assignmentperformancedata7={
    full_name: "Arpit Mathur",
    score: 79
}
var mock_assignmentperformancedata8={
    full_name: "Rutwik Dhongde",
    score: 83
}

var mock_assignmentperformancedata9={
    full_name: "Shlok Singh",
    score: 11
}

var mock_assignmentperformancedata10={
    full_name: "Kanye West",
    score: 32
}

var mock_assignmentperformancedata11={
    full_name: "Lorem Ipsum",
    score: 73
}


var mock_subjectroomdata1={
    subject_room: "8-A Mathematics",
    subject_teacher: "Anjali Lal",
    listing:[
        {
            date: "July 20",
            topic: "Mensuration",
            subjectroom_average: 85,
            class_average:83
        },
        {
            date: "July 22",
            topic: "Triangles",
            subjectroom_average: 88,
            class_average:81
        },
        {
            date: "July 23",
            topic: "Basics of Geometry",
            subjectroom_average: 81,
            class_average:90
        },
        {
            date: "July 24",
            topic: "Linear equations",
            subjectroom_average: 91,
            class_average:84
        },
        {
            date: "July 29",
            topic: "Quadratic equations",
            subjectroom_average: 83,
            class_average:86
        }
    ]
}
var mock_subjectroomdata2={
    subject_room: "8-B Mathematics",
    subject_teacher: "Pujan Parikh",
    listing:[
        {
            date: "July 20",
            topic: "Mensuration",
            subjectroom_average: 95,
            class_average:83
        },
        {
            date: "July 22",
            topic: "Triangles",
            subjectroom_average: 84,
            class_average:81
        },
        {
            date: "July 23",
            topic: "Basics of Geometry",
            subjectroom_average: 88,
            class_average:90
        },
        {
            date: "July 24",
            topic: "Linear equations",
            subjectroom_average: 90,
            class_average:84
        },
        {
            date: "July 29",
            topic: "Quadratic equations",
            subjectroom_average: 87,
            class_average:86
        }
    ]
}
var mock_subjectroomdata3={
    subject_room: "8-C Mathematics",
    subject_teacher: "Hrishikesh Rao",
    listing:[
        {
            date: "July 20",
            topic: "Mensuration",
            subjectroom_average: 99,
            class_average:83
        },
        {
            date: "July 22",
            topic: "Triangles",
            subjectroom_average: 98,
            class_average:81
        },
        {
            date: "July 23",
            topic: "Basics of Geometry",
            subjectroom_average: 94,
            class_average:90
        },
        {
            date: "July 24",
            topic: "Linear equations",
            subjectroom_average: 98,
            class_average:84
        },
        {
            date: "July 29",
            topic: "Quadratic equations",
            subjectroom_average: 100,
            class_average:86
        }
    ]
}
var mock_subjectroomdata4={
    subject_room: "8-D Mathematics",
    subject_teacher: "Oasis Vali",
    listing:[
        {
            date: "July 20",
            topic: "Mensuration",
            subjectroom_average: 78,
            class_average:83
        },
        {
            date: "July 22",
            topic: "Triangles",
            subjectroom_average: 86,
            class_average:81
        },
        {
            date: "July 23",
            topic: "Basics of Geometry",
            subjectroom_average: 89,
            class_average:90
        },
        {
            date: "July 24",
            topic: "Linear equations",
            subjectroom_average: 75,
            class_average:84
        },
        {
            date: "July 29",
            topic: "Quadratic equations",
            subjectroom_average: 100,
            class_average:86
        }
    ]
}

var mock_studentdata={
    performance_report:{    
        class_teacher: "Oasis Vali",
        listing: [ 
            { 
                subject:"Mathematics",
                student_average: 56,
                class_average:83
            },
            {
                subject:"Science",
                student_average:82,
                class_average:77,
            },
            {
                subject:"Social Studies",
                student_average:88,
                class_average:81,
            },
            {
                subject:"English",
                student_average:91,
                class_average:88,
            },
            {
                subject:"Second Language",
                student_average:95,
                class_average:97,
            },
            {
                subject:"FIT",
                student_average:84,
                class_average:89,
            }
        ]   
    },

    breakdown_listing:[
        {
            subject:"Mathematics",
            subject_teacher:"Anjali Lal",
            listing:[
                {
                    date: "July 18",
                    topic: "Complex Numbers",
                    class_average: 81,
                    student_score: 88
                },
                {
                    date: "July 19",
                    topic: "Series and Sequences",
                    class_average: 84,
                    student_score: 86
                },
                {
                    date: "July 20",
                    topic: "Integration",
                    class_average: 94,
                    student_score: 96
                },
                {
                    date: "July 21",
                    topic: "3D Geometry",
                    class_average: 95,
                    student_score: 91
                },
                {
                    date: "July 23",
                    topic: "Probability",
                    class_average: 77,
                    student_score: 82
                }
            ]    
        },
        {
            subject:"Science",
            subject_teacher:"Amita Singh",
            listing:[
                {
                    date: "July 18",
                    topic: "Organic Chemistry",
                    class_average: 89,
                    student_score: 83
                },
                {
                    date: "July 19",
                    topic: "Atoms and Molecules",
                    class_average: 83,
                    student_score: 28
                },
                {
                    date: "July 21",
                    topic: "Redox Reactions",
                    class_average: 74,
                    student_score: 91
                },
                {
                    date: "July 22",
                    topic: "Nuclear Chemistry",
                    class_average: 87,
                    student_score: 99
                },
                {
                    date: "July 24",
                    topic: "Environmental Chemistry",
                    class_average: 81,
                    student_score: 77
                }
            ]    
        },
        {
            subject:"Social Studies",
            subject_teacher:"Rama Kumar",
            listing:[
                {
                    date: "July 17",
                    topic: "India Geography",
                    class_average: 89,
                    student_score: 82
                },
                {
                    date: "July 19",
                    topic: "Pre-independent India",
                    class_average: 70,
                    student_score: 88
                },
                {
                    date: "July 20",
                    topic: "Politics in India",
                    class_average: 83,
                    student_score: 95
                },
                {
                    date: "July 20",
                    topic: "Natural Resources",
                    class_average: 92,
                    student_score: 97
                },
                {
                    date: "July 23",
                    topic: "Books of the Past",
                    class_average: 84,
                    student_score: 94
                }
            ]   
        },
        {
            subject:"English",
            subject_teacher:"Shivani Lal",
            listing:[
                {
                    date: "July 16",
                    topic: "Ghost of Canterville",
                    class_average: 87,
                    student_score: 91
                },
                {
                    date: "July 18",
                    topic: "Tale of Two cities",
                    class_average: 82,
                    student_score: 88
                },
                {
                    date: "July 19",
                    topic: "Ranga's Marriage",
                    class_average: 94,
                    student_score: 96
                },
                {
                    date: "July 21",
                    topic: "Wolf Grey",
                    class_average: 89,
                    student_score: 100
                },
                {
                    date: "July 23",
                    topic: "Lorum Ipsum",
                    class_average: 71,
                    student_score: 72
                }
            ]    
        },
        {
            subject:"Second Language",
            subject_teacher:"Swagata Rudra",
            listing:[
                {
                    date: "July 18",
                    topic: "Shlokas",
                    class_average: 74,
                    student_score: 99
                },
                {
                    date: "July 19",
                    topic: "Vedas",
                    class_average: 84,
                    student_score: 80
                },
                {
                    date: "July 20",
                    topic: "Yajurveda",
                    class_average: 87,
                    student_score: 92
                },
                {
                    date: "July 20",
                    topic: "Atharvaveda",
                    class_average: 93,
                    student_score: 90
                },
                {
                    date: "July 25",
                    topic: "Sandhi",
                    class_average: 92,
                    student_score: 96
                }
            ]   
        },
        {
            subject:"FIT",
            subject_teacher:"Sandeep Raut",
            listing:[
                {
                    date: "July 17",
                    topic: "Binary Representation",
                    class_average: 95,
                    student_score: 99
                },
                {
                    date: "July 19",
                    topic: "Basics of HTML",
                    class_average: 10,
                    student_score: 100
                },
                {
                    date: "July 20",
                    topic: "Basics of XML",
                    class_average: 73,
                    student_score: 82
                },
                {
                    date: "July 21",
                    topic: "JSON introduction",
                    class_average: 87,
                    student_score: 76
                },
                {
                    date: "July 25",
                    topic: "Concepts of Javascript",
                    class_average: 82,
                    student_score: 77
                }
            ]
        }
    ]
}
var studentdata=new Performance(mock_studentdata);

var subjectroomdata1 = new SubjectroomPerformanceBreakdown(mock_subjectroomdata1);
var subjectroomdata2 = new SubjectroomPerformanceBreakdown(mock_subjectroomdata2);
var subjectroomdata3 = new SubjectroomPerformanceBreakdown(mock_subjectroomdata3);
var subjectroomdata4 = new SubjectroomPerformanceBreakdown(mock_subjectroomdata4);

var subjectroomarray=[subjectroomdata1,subjectroomdata2,subjectroomdata3,subjectroomdata4];

var assignmentstudent1= new AssignmentPerformanceElement(mock_assignmentperformancedata1);
var assignmentstudent2= new AssignmentPerformanceElement(mock_assignmentperformancedata2);
var assignmentstudent3= new AssignmentPerformanceElement(mock_assignmentperformancedata3);
var assignmentstudent4= new AssignmentPerformanceElement(mock_assignmentperformancedata4);
var assignmentstudent5= new AssignmentPerformanceElement(mock_assignmentperformancedata5);
var assignmentstudent6= new AssignmentPerformanceElement(mock_assignmentperformancedata6);
var assignmentstudent7= new AssignmentPerformanceElement(mock_assignmentperformancedata7);
var assignmentstudent8= new AssignmentPerformanceElement(mock_assignmentperformancedata8);
var assignmentstudent9= new AssignmentPerformanceElement(mock_assignmentperformancedata9);
var assignmentstudent10= new AssignmentPerformanceElement(mock_assignmentperformancedata10);
var assignmentstudent11= new AssignmentPerformanceElement(mock_assignmentperformancedata11);

var assignmentarray=[assignmentstudent1,assignmentstudent2,assignmentstudent3,assignmentstudent4,assignmentstudent5,assignmentstudent6,assignmentstudent7,assignmentstudent8,assignmentstudent9,assignmentstudent10,assignmentstudent11];